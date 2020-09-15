import json
import jinja2
import sys

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
from urllib.parse import quote
from functions import generate_html_file, get_bugs_dict, \
	get_bugs_set, get_jenkins_job_info, get_jenkins_jobs, \
	get_jira_dict, get_jira_set, get_osp_version, \
	get_other_blockers, percent


def run_report(config, blockers, server, header, test_email, no_email, template_file):

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
	all_tickets_set = get_jira_set(blockers) if blockers else {}

	# Create dictionary from the set of all jira tickets with ticket id as key and name and link as value
	all_jira_dict = get_jira_dict(all_tickets_set, config)

	# iterate through all relevant jobs and build report rows
	num_success = 0
	num_unstable = 0
	num_failure = 0
	num_missing = 0
	num_aborted = 0
	num_error = 0
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
		jenkins_api_info = get_jenkins_job_info(server, job_name)

		# if jeeves was unable to collect any good jenkins api info, skip job
		if jenkins_api_info:

			# take action based on last completed build result
			if jenkins_api_info['lcb_result'] in ["SUCCESS", "NO_KNOWN_BUILDS", "ABORTED"]:
				if jenkins_api_info['lcb_result'] == "SUCCESS":
					num_success += 1
				elif jenkins_api_info['lcb_result'] == "NO_KNOWN_BUILDS":
					num_missing += 1
				else:
					num_aborted += 1

				bugs = [{'bug_name': 'N/A', 'bug_url': None}]
				tickets = [{'ticket_name': 'N/A', 'ticket_url': None}]
				other = [{'other_name': 'N/A', 'other_url': None}]

			elif jenkins_api_info['lcb_result'] in ["UNSTABLE", "FAILURE"]:
				if jenkins_api_info['lcb_result'] == "UNSTABLE":
					num_unstable += 1
				else:
					num_failure += 1

				# get all related bugs to job
				try:
					bug_ids = blockers[job_name]['bz']
					all_bugs.extend(bug_ids)
					bugs = list(map(all_bugs_dict.get, bug_ids))
				except:
					bugs = [{'bug_name': "Could not find relevant bug", 'bug_url': None}]

				# get all related tickets to job
				try:
					ticket_ids = blockers[job_name]['jira']
					all_tickets.extend(ticket_ids)
					tickets = list(map(all_jira_dict.get, ticket_ids))
				except:
					tickets = [{'ticket_name': "Could not find relevant ticket", 'ticket_url': None}]

				# get any "other" artifact for job
				try:
					other = get_other_blockers(blockers, job_name)
				except:
					other = [{'other_name': 'N/A', 'other_url': None}]

			else:
				print("job {} had lcb_result {}: reporting as error job".format(job_name, jenkins_api_info['lcb_result']))
				jenkins_api_info['lcb_result'] = "ERROR"
				num_error += 1
				bugs = [{'bug_name': 'N/A', 'bug_url': None}]
				tickets = [{'ticket_name': 'N/A', 'ticket_url': None}]
				other = [{'other_name': 'N/A', 'other_url': None}]

			# build row
			row = {
				'osp_version': osp_version,
				'job_name': job_name,
				'build_days_ago': jenkins_api_info['build_days_ago'],
				'job_url': jenkins_api_info['job_url'],
				'lcb_num': jenkins_api_info['lcb_num'],
				'lcb_url': jenkins_api_info['lcb_url'],
				'compose': jenkins_api_info['compose'],
				'lcb_result': jenkins_api_info['lcb_result'],
				'bugs': bugs,
				'tickets': tickets,
				'other': other
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

	# create chart config
	chart_config = {
		'type': 'doughnut',
		'data': {
			'labels': ['Success', 'Aborted', 'Failure', 'Error', 'Unstable', 'Missing'],
			'datasets': [{
				'backgroundColor': ['blue', 'black', 'red', 'brown', 'yellow', 'grey'],
				'data': [num_success, num_aborted, num_failure, num_error, num_unstable, num_missing]
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

	chart_config = {
		'type': 'doughnut',
		'data': {
			'labels': ['Success', 'Unstable', 'Failed', 'Aborted', 'Error', 'Missing'],
			'datasets': [{
				'data': [num_success, num_unstable, num_failure, num_aborted, num_error, num_missing]
			}]
		},
		'options': {
		  	'plugins': {
		    	'datalabels': {
				'display': 'true',
				'backgroundColor': ['green', 'yellow', 'red', 'grey', 'brown', 'purple'],
		    	'borderRadius': 3,
		    	'font': {
					'color': 'red',
		        	'weight': 'bold',
		    	}
		    	},
		    'doughnutlabel': {
		      	'labels': [{
		        'text': num_jobs,
		        'font': {
		        	'size': 20,
		        	'weight': 'bold',
		        }
		    	}, {
		        	'text': 'Total Jobs'
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

	# include missing report if needed
	if num_missing > 0:
		summary['total_missing'] = "Total NO_KNOWN_BUILDS:  {}/{} = {}%".format(num_missing, num_jobs, percent(num_missing, num_jobs))
	else:
		summary['total_missing'] = False

	# include abort report if needed
	if num_aborted > 0:
		summary['total_aborted'] = "Total ABORTED:  {}/{} = {}%".format(num_aborted, num_jobs, percent(num_aborted, num_jobs))
	else:
		summary['total_aborted'] = False

	# include error report if needed
	if num_error > 0:
		summary['total_error'] = "Total ERROR:  {}/{} = {}%".format(num_error, num_jobs, percent(num_error, num_jobs))
	else:
		summary['total_error'] = False

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
			msg['From'] = header['user_email_address']
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
