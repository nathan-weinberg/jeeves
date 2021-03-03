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


def percent(part, whole):
	''' basic percent function
	'''
	return round(100 * float(part) / float(whole), 1)


def validate_config(config, no_email):
	''' validates config fields
		raises exception if required field is not present
	'''
	required_fields = [
		'jenkins_url',
		'job_search_fields',
		'bz_url',
		'jira_url',
		'certificate'
	]

	if not no_email:
		required_fields.append('email_from')
		required_fields.append('email_subject')
		required_fields.append('email_to')
		required_fields.append('smtp_host')

	for field in required_fields:
		if config.get(field) is None:
			raise Exception('field "{}" is not defined'.format(field))
	return None
