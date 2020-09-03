import sys
import json
import jinja2

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
from urllib.parse import quote

from jeeves.common import generate_html_file, percent
from jeeves.jobs import get_jenkins_job_info, get_jenkins_jobs, get_osp_version
from jeeves.blockers import get_bugs_dict, get_bugs_set, get_tickets_dict, get_tickets_set, get_other_blockers


def run_report(config, blockers, preamble_file, server, header, test_email, no_email, template_file):

	# fetch all relevant jobs
	jobs = get_jenkins_jobs(server, config['job_search_fields'])

	# log and exit if no jobs found - no reason to send empty report
	num_jobs_fetched = len(jobs)
	if num_jobs_fetched == 0:
		print("No jobs found with given search field. Exiting...")
		return None

	# Get set from the list of all bugs in all jobs
	all_bugs_set = get_bugs_set(blockers) if blockers else {}

	# Create dictionary the set of all bugs with bug id as key and name and link as value
	all_bugs_dict = get_bugs_dict(all_bugs_set, config)

	# Get set from the list of all jira-tickets in all jobs
	all_tickets_set = get_tickets_set(blockers) if blockers else {}

	# Create dictionary from the set of all jira tickets with ticket id as key and name and link as value
	all_tickets_dict = get_tickets_dict(all_tickets_set, config)

	# fetch optional config options, return None if not present
	fpn = config.get('filter_param_name', None)
	fpv = config.get('filter_param_value', None)

	# iterate through all relevant jobs and build report rows
	num_success = 0
	num_unstable = 0
	num_failure = 0
	num_missing = 0
	num_aborted = 0
	num_error = 0
	num_covered = 0
	rows = []
	all_bugs = []
	all_tickets = []
	for job in jobs:

		# get name and osp version from job object
		job_name = job['name']
		osp_version = get_osp_version(job_name)

		# skip if no OSP version could be found
		if osp_version is None:
			print('No OSP version could be found in job {}. Skipping...'.format(job_name))
			continue

		# get job info from jenkins API - will return False if an unmanageable error occured
		jenkins_api_info = get_jenkins_job_info(server, job_name, filter_param_name=fpn, filter_param_value=fpv)

		# if jeeves was unable to collect any good jenkins api info, skip job
		if jenkins_api_info:

			# take action based on last completed build result
			if jenkins_api_info['lcb_result'] == "SUCCESS":
				num_success += 1
				bugs = []
				tickets = []
				other = []

			elif jenkins_api_info['lcb_result'] in ["UNSTABLE", "FAILURE", "ABORTED", "NO_KNOWN_BUILDS"]:
				if jenkins_api_info['lcb_result'] == "UNSTABLE":
					num_unstable += 1
				elif jenkins_api_info['lcb_result'] == "FAILURE":
					num_failure += 1
				elif jenkins_api_info['lcb_result'] == "ABORTED":
					num_aborted += 1
				else:
					num_missing += 1

				# get all related bugs to job
				job_covered = False
				try:
					bug_ids = blockers[job_name]['bz']
					if 0 in bug_ids:
						bug_ids.remove(0)
					all_bugs.extend(bug_ids)
					bugs = list(map(all_bugs_dict.get, bug_ids))
					job_covered = True
				except Exception as e:
					print("Error fetching bugs for job {}: {}".format(job_name, e))
					bugs = []

				# get all related tickets to job
				try:
					ticket_ids = blockers[job_name]['jira']
					if 0 in ticket_ids:
						ticket_ids.remove(0)
					all_tickets.extend(ticket_ids)
					tickets = list(map(all_tickets_dict.get, ticket_ids))
					job_covered = True
				except Exception as e:
					print("Error fetching tickets for job {}: {}".format(job_name, e))
					tickets = []

				# get any "other" artifact for job
				try:
					other = get_other_blockers(blockers, job_name)
					job_covered = True
				except Exception as e:
					print("Error fetching other blockers for job {}: {}".format(job_name, e))
					other = []

				if job_covered:
					num_covered += 1
			else:
				print("job {} had lcb_result {}: reporting as error job".format(job_name, jenkins_api_info['lcb_result']))
				jenkins_api_info['lcb_result'] = "ERROR"
				num_error += 1
				bugs = []
				tickets = []
				other = []

			# check if row contains any valid blockers for reporting
			blocker_bool = True
			if (len(bugs) == 0) and (len(tickets) == 0) and (len(other) == 0):
				blocker_bool = False

			# build row
			row = {
				'osp_version': osp_version,
				'job_name': job_name,
				'build_days_ago': jenkins_api_info['build_days_ago'],
				'job_url': jenkins_api_info['job_url'],
				'lcb_num': jenkins_api_info['lcb_num'],
				'lcb_url': jenkins_api_info['lcb_url'],
				'compose': jenkins_api_info['compose'],
				'second_compose': jenkins_api_info['second_compose'],
				'lcb_result': jenkins_api_info['lcb_result'],
				'blocker_bool': blocker_bool,
				'bugs': bugs,
				'tickets': tickets,
				'other': other,
				'tempest_tests_failed': jenkins_api_info['tempest_tests_failed'],
				'tempest_tests_url': jenkins_api_info['job_url'] + str(jenkins_api_info['lcb_num']) + '/testReport'
			}

			# append row to rows
			rows.append(row)

	# sort rows by descending OSP version
	rows = sorted(rows, key=lambda row: row['osp_version'], reverse=True)

	# log and exit if no rows built - otherwise program will crash on summary generation
	num_jobs = len(rows)
	if num_jobs == 0:
		print("No rows could be built with data for any of the jobs found with given search field. Exiting...")
		return None

	# initialize summary
	summary = {}

	# job result metrics
	summary['total_success'] = "Total SUCCESS:  {}/{} = {}%".format(num_success, num_jobs, percent(num_success, num_jobs))
	summary['total_unstable'] = "Total UNSTABLE: {}/{} = {}%".format(num_unstable, num_jobs, percent(num_unstable, num_jobs))
	summary['total_failure'] = "Total FAILURE:  {}/{} = {}%".format(num_failure, num_jobs, percent(num_failure, num_jobs))
	summary['total_coverage'] = "Total bz/jira/other coverage:  {}/{} = {}%".format(num_covered, num_jobs-num_success, percent(num_covered, num_jobs-num_success))

	# Map color codes with job count and type
	jobs_dict = {
		'#3465a4': (num_success, 'Success'),
		'#515151': (num_aborted, 'Aborted'),
		'#ef2929': (num_failure, 'Failure'),
		'#704426': (num_error, 'Error'),
		'#ffb738': (num_unstable, 'Unstable'),
		'#bbbbbb': (num_missing, 'Missing')
	}

	# Filter only available jobs
	bg_color_list, data_list, labels_list = [], [], []
	for key, (job_count, job_label) in jobs_dict.items():
		if job_count != 0:
			bg_color_list.append(key)
			data_list.append(job_count)
			labels_list.append(job_label)

	# create chart config
	chart_config = {
		'type': 'doughnut',
		'data': {
			'labels': labels_list,
			'datasets': [{
				'backgroundColor': bg_color_list,
				'data': data_list
			}]
		},
		'options': {
			'plugins': {
				'datalabels': {
					'display': 'true',
					'align': 'middle',
					'backgroundColor': '#fff',
					'borderRadius': 20,
					'font': {
						'weight': 'bold',
					}
				},
				'doughnutlabel': {
					'labels': [{
						'text': num_jobs,
						'font': {
							'size': 20,
						}
					}, {
						'text': 'Total Jobs',
						'font': {
							'size': 15,
						}
					}]
				}
			}
		}
	}
	encoded_config = quote(json.dumps(chart_config))
	summary['chart_url'] = f'https://quickchart.io/chart?c={encoded_config}'

	# bug metrics
	all_bugs = [bug_id for bug_id in all_bugs if bug_id != 0]
	if len(all_bugs) == 0:
		summary['total_bugs'] = "Blocker Bugs: 0 total"
	else:
		unique_bugs = set(all_bugs)
		summary['total_bugs'] = "Blocker Bugs: {} total, {} unique".format(len(all_bugs), len(unique_bugs))

	# ticket metrics
	all_tickets = [ticket_id for ticket_id in all_tickets if ticket_id != 0]
	if len(all_tickets) == 0:
		summary['total_tickets'] = "Blocker Tickets: 0 total"
	else:
		unique_tickets = set(all_tickets)
		summary['total_tickets'] = "Blocker Tickets: {} total, {} unique".format(len(all_tickets), len(unique_tickets))

	# include abort report if needed
	if num_aborted > 0:
		summary['total_aborted'] = "Total ABORTED:  {}/{} = {}%".format(num_aborted, num_jobs, percent(num_aborted, num_jobs))
	else:
		summary['total_aborted'] = False

	# include missing report if needed
	if num_missing > 0:
		summary['total_missing'] = "Total NO_KNOWN_BUILDS:  {}/{} = {}%".format(num_missing, num_jobs, percent(num_missing, num_jobs))
	else:
		summary['total_missing'] = False

	# include error report if needed
	if num_error > 0:
		summary['total_error'] = "Total ERROR:  {}/{} = {}%".format(num_error, num_jobs, percent(num_error, num_jobs))
	else:
		summary['total_error'] = False

	# load a preamble for injection if specified
	preamble = None
	if preamble_file:
		with open(preamble_file, 'r') as file:
			preamble = file.read()

	# initialize jinja2 vars
	loader = jinja2.FileSystemLoader('./templates')
	env = jinja2.Environment(loader=loader)
	try:
		template = env.get_template(template_file)
	except Exception as e:
		print("Error loading template file: {}\n{}".format(template_file, e))
		sys.exit(1)

	# generate HTML report
	htmlcode = template.render(
		header=header,
		preamble=preamble,
		rows=rows,
		summary=summary
	)

	# save HTML report to file if not test run
	if not test_email:
		filename = generate_html_file(htmlcode)
		print('HTML file generated as {}'.format(filename))

	# if "no email" flag has been passed, do not execute this block
	if not no_email:
		try:

			# parse list of email addresses
			if test_email:
				recipients = config['email_to_test'].split(',')
			else:
				recipients = config['email_to'].split(',')

			# construct email
			msg = MIMEMultipart()
			msg['From'] = config['email_from']
			msg['Subject'] = config['email_subject']
			msg['To'] = ", ".join(recipients)
			msg.attach(MIMEText(htmlcode, 'html'))

			# create SMTP session
			with SMTP(config['smtp_host']) as smtp:

				# start TLS for security
				smtp.starttls()

				# use ehlo or helo if needed
				smtp.ehlo_or_helo_if_needed()

				# send email to all addresses
				response = smtp.sendmail(msg['From'], recipients, msg.as_string())

				# log success if all recipients recieved report, otherwise raise exception
				if response == {}:
					print("Report successfully accepted by mail server for delivery")
				else:
					raise Exception("Mail server cannot deliver report to following recipients: {}".format(response))

		except Exception as e:
			print('Error sending email report: {}\nSee HTML file saved in "archive" folder'.format(e))
