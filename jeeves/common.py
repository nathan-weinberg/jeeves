# common functions used throughout jeeves

import os
import datetime


def generate_header(source, filter_param_name=None, filter_param_value=None, remind=False):
	''' generates header
		optionally takes name and value of jenkins param to filter builds by
		if remind is true, header source should be blocker_file
		if remind is false, header source should be job_search_fields
	'''
	date = '{:%m/%d/%Y at %I:%M%p %Z}'.format(datetime.datetime.now())

	# show only filename in remind header, not full path
	if remind:
		source = source.rsplit('/', 1)[-1]

	header = {
		'date': date,
		'source': source,
		'fpn': filter_param_name,
		'fpv': filter_param_value
	}
	return header


def generate_html_file(htmlcode, remind=False):
	''' generates HTML file of reminder
	'''
	try:
		os.makedirs('archive')
	except FileExistsError:
		pass
	reportType = 'reminder' if remind else 'report'
	filename = './archive/{}_{:%Y-%m-%d_%H-%M-%S}.html'.format(
		reportType, datetime.datetime.now())
	with open(filename, 'w') as file:
		file.write(htmlcode)
	return filename


def generate_failure_stage_log_urls(config, err_stage, job_url, lcb_num):
	''' generates list of urls for failed build stages
	'''
	stage_urls = []
	if 'stage_logs' in config and err_stage in config['stage_logs']:
		for path in config['stage_logs'][err_stage]:
			stage_urls.append("{}/{}/artifact/{}".format(job_url, lcb_num, path))
	if not stage_urls:
		stage_urls = None
	return stage_urls


def percent(part, whole):
	''' basic percent function
	'''
	return round(100 * float(part) / float(whole), 1)


def validate_config(config, no_email, test_email):
	''' validates config fields
		raises exception if required field is not present
	'''

	# these fields are always required
	required_fields = [
		'jenkins_url',
		'job_search_fields',
		'bz_url',
		'jira_url',
		'certificate'
	]

	# fields only required if user is sending email
	if not no_email:
		required_fields.append('smtp_host')
		required_fields.append('email_subject')
		required_fields.append('email_from')
		required_fields.append('email_to')

	# fields only required if user is sending test email
	if test_email:
		required_fields.append('email_to_test')

	# check for all required fields
	for field in required_fields:
		if config.get(field) is None:
			raise Exception('field "{}" is not defined'.format(field))

	return None
