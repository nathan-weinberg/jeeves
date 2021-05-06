import jinja2

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP

from jeeves.common import generate_html_file
from jeeves.jobs import get_jenkins_job_info, get_osp_version, generate_failure_stage_log_urls
from jeeves.blockers import get_bugs_dict, get_tickets_dict, get_other_blockers


def run_remind(config, blockers, server, header):

	# get list of all owners in blocker file
	owner_list = []
	for job in blockers:
		owners = blockers[job].get('owners', False)
		if not owners:
			continue
		owner_list.extend(owners)

	# exit if no owners are found for any jobs in blockers file
	if owner_list == []:
		print("No owners found in blocker file")
		return None

	# fetch optional config options, return None if not present
	fpn = config.get('filter_param_name', None)
	fpv = config.get('filter_param_value', None)
	cac = config.get('cause_action_class', None)

	# find each job with no blockers including the owner and send email with agg'd list
	owner_set = set(owner_list)
	for owner in owner_set:
		rows = []
		for job_name in blockers:
			owners = blockers[job_name].get('owners', [])
			osp_version = get_osp_version(job_name)

			# skip if current owner is not owner of this job
			if owner not in owners:
				continue

			# get job info from jenkins API - will return False if an unmanageable error occured
			jenkins_api_info = get_jenkins_job_info(server, job_name, filter_param_name=fpn, filter_param_value=fpv, cause_action_class=cac)

			# if jeeves was unable to collect any good jenkins API info, skip job
			if jenkins_api_info:

				# only care about jobs without SUCCESS status
				if jenkins_api_info['lcb_result'] != "SUCCESS":

					# get all related bugs to job
					try:
						bug_ids = blockers[job_name]['bz']
						if 0 in bug_ids:
							bug_ids.remove(0)
						bugs_dict = get_bugs_dict(bug_ids, config)
						bugs = list(map(bugs_dict.get, bug_ids))
					except Exception as e:
						print("Error fetching bugs for job {}: {}".format(job_name, e))
						bugs = []

					# get all related tickets to job
					try:
						ticket_ids = blockers[job_name]['jira']
						if 0 in ticket_ids:
							ticket_ids.remove(0)
						tickets_dict = get_tickets_dict(ticket_ids, config)
						tickets = list(map(tickets_dict.get, ticket_ids))
					except Exception as e:
						print("Error fetching ticket for job {}: {}".format(job_name, e))
						tickets = []

					# get any "other" artifact for job
					try:
						other = get_other_blockers(blockers, job_name)
					except Exception as e:
						print("Error fetching other blockers for job {}: {}".format(job_name, e))
						other = []

					# check if row contains any valid blockers for reporting
					blocker_bool = True
					if (len(bugs) == 0) and (len(tickets) == 0) and (len(other) == 0):
						blocker_bool = False

					stage_urls = []
					if jenkins_api_info['stage_failure'] != 'N/A':
						stage_urls = generate_failure_stage_log_urls(
							config,
							jenkins_api_info['stage_failure'],
							jenkins_api_info['job_url'],
							jenkins_api_info['lcb_num']
						)

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
						'tempest_tests_url': jenkins_api_info['job_url'] + str(jenkins_api_info['lcb_num']) + '/testReport',
						'stage_name': jenkins_api_info['stage_failure'],
						'stage_urls': stage_urls
					}

					# append row to rows
					rows.append(row)

		# if no rows were generated, owner has all passing jobs
		if rows != []:

			# sort rows by descending OSP version
			rows = sorted(rows, key=lambda row: row['osp_version'], reverse=True)

			# initialize jinja2 vars
			loader = jinja2.FileSystemLoader('./templates')
			env = jinja2.Environment(loader=loader)
			template = env.get_template('remind_template.html')

			# generate HTML report
			htmlcode = template.render(
				header=header,
				rows=rows
			)

			# construct email
			msg = MIMEMultipart()
			msg['From'] = config['email_from']
			msg['Subject'] = "Jeeves Reminder for {}".format(owner)
			msg['To'] = owner
			msg.attach(MIMEText(htmlcode, 'html'))

			# create SMTP session - if jeeves is unable to do so an HTML file will be generated
			try:
				with SMTP(config['smtp_host']) as smtp:

					# start TLS for security
					smtp.starttls()

					# use ehlo or helo if needed
					smtp.ehlo_or_helo_if_needed()

					# send email to all addresses
					response = smtp.sendmail(msg['From'], msg['To'], msg.as_string())

					# log success if all recipients recieved reminder, otherwise raise exception
					if response == {}:
						print("Reminder for {} successfully accepted by mail server for delivery".format(owner))
					else:
						raise Exception("Mail server cannot deliver reminder to following recipients: {}".format(response))

			except Exception as e:
				print("Error sending email reminder: {}\nHTML file generated".format(e))
				generate_html_file(htmlcode, remind=True)

		else:
			print("Owner {} has all passing jobs!".format(owner))
