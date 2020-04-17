import jinja2
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functions import generate_html_file, get_osp_version, has_blockers


def run_remind(config, blockers, server, header):

	# get set of all owners in blocker file
	owner_list = []
	for job in blockers:
		owners = blockers[job].get('owners', False)
		if not owners:
			continue
		owner_list.extend(owners)
	owner_set = set(owner_list)

	# find each job with no blockers including the owner and send email with agg'd list
	for owner in owner_set:
		rows = []
		for job_name in blockers:
			owners = blockers[job_name].get('owners', [])
			if owner not in owners:
				continue
			osp_version = get_osp_version(job_name)

			# get all relevant info from jenkins
			try:
				job_info = server.get_job_info(job_name)
				job_url = job_info['url']
				lcb_num = job_info['lastCompletedBuild']['number']
				build_info = server.get_build_info(job_name, lcb_num)
				build_actions = build_info['actions']
				component = [action['text'] for action in build_actions if 'COMPONENT' in action.get('text', '')]

				# if build was testing specific component, find next most recent build not testing a component
				while component != []:
					lcb_num = lcb_num - 1
					build_info = server.get_build_info(job_name, lcb_num)
					build_actions = build_info['actions']
					component = [action['text'] for action in build_actions if 'COMPONENT' in action.get('text', '')]

				lcb_url = build_info['url']
				lcb_result = build_info['result']
				compose = [action['text'][13:-4] for action in build_actions if 'core_puddle' in action.get('text', '')]

				# No compose could be found; likely a failed job where the 'core_puddle' var was never calculated
				if compose == []:
					compose = "Could not find compose"
				else:
					compose = compose[0]

			except Exception as e:

				# No "Last Completed Build" found
				if job_info['builds'] == []:
					lcb_num = None
					compose = "N/A"
					lcb_url = None
					lcb_result = "NO_KNOWN_BUILDS"

				# Unknown error, skip job
				else:
					print("Jenkins API call error on job {}: {}".format(job_name, e))
					continue

			# only care about jobs with UNSTABLE or FAILURE status that have no blockers
			if lcb_result == "UNSTABLE" or lcb_result == "FAILURE":
				if not has_blockers(blockers, job_name):
					row = {
						'osp_version': osp_version,
						'job_name': job_name,
						'job_url': job_url,
						'lcb_num': lcb_num,
						'lcb_url': lcb_url,
						'compose': compose,
						'lcb_result': lcb_result,
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
					smtp.sendmail(msg['From'], msg['To'], msg.as_string())

			except Exception as e:
				print("Error sending email report: {}\nHTML file generated".format(e))
				generate_html_file(htmlcode, remind=True)

		else:
			print("Owner {} has no untriaged jobs!".format(owner))
