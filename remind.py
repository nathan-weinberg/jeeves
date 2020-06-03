import jinja2
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functions import generate_html_file, get_osp_version, \
	get_jenkins_job_info


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

			# get job info from jenkins API
			jenkins_api_info = get_jenkins_job_info(server, job_name)

			# if jeeves was unable to collect any good jenkins API info, skip job
			if jenkins_api_info:

				# only care about jobs with UNSTABLE or FAILURE status that have no blockers
				if jenkins_api_info['lcb_result'] == "UNSTABLE" or jenkins_api_info['lcb_result'] == "FAILURE":
					row = {
						'osp_version': osp_version,
						'job_name': job_name,
						'job_url': jenkins_api_info['job_url'],
						'lcb_num': jenkins_api_info['lcb_num'],
						'lcb_url': jenkins_api_info['lcb_url'],
						'compose': jenkins_api_info['compose'],
						'lcb_result': jenkins_api_info['lcb_result'],
					}
					rows.append(row)

		# if no rows were generated, all jobs belonging to owner are already triaged
		if rows != []:

			# initialize jinja2 vars
			loader = jinja2.FileSystemLoader('./remind_template.html')
			env = jinja2.Environment(loader=loader)
			template = env.get_template('')

			# generate HTML report
			htmlcode = template.render(
				header=header,
				rows=rows
			)

			# construct email
			msg = MIMEMultipart()
			msg['From'] = header['user_email_address']
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
						print("Reminder successfully accepted by mail server for delivery")
					else:
						raise Exception("Mail server cannot deliver reminder to following recipients: {}".format(response))

			except Exception as e:
				print("Error sending email reminder: {}\nHTML file generated".format(e))
				generate_html_file(htmlcode, remind=True)

		else:
			print("Owner {} has no untriaged jobs!".format(owner))
