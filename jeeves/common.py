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


def generate_summary(num_success, num_unstable, num_failure, num_aborted, num_missing, num_error, num_jobs):
	""" generates summary based on given parameters
		overall summary does not display total jobs as this is done in piechart
		summary per version displays all fields
	"""

	# initialize empty summary
	summary = {}

	# populate summary with job result data
	summary['total_jobs'] = "Total number of jobs: {}".format(num_jobs)
	summary['total_success'] = "SUCCESS:  {}/{} = {}%".format(num_success, num_jobs, percent(num_success, num_jobs))
	summary['total_unstable'] = "UNSTABLE: {}/{} = {}%".format(num_unstable, num_jobs, percent(num_unstable, num_jobs))
	summary['total_failure'] = "FAILURE:  {}/{} = {}%".format(num_failure, num_jobs, percent(num_failure, num_jobs))

	# include abort report if needed
	if num_aborted > 0:
		summary['total_aborted'] = "ABORTED:  {}/{} = {}%".format(num_aborted, num_jobs, percent(num_aborted, num_jobs))
	else:
		summary['total_aborted'] = False

	# include missing report if needed
	if num_missing > 0:
		summary['total_missing'] = "NO_KNOWN_BUILDS:  {}/{} = {}%".format(num_missing, num_jobs, percent(num_missing, num_jobs))
	else:
		summary['total_missing'] = False

	# include error report if needed
	if num_error > 0:
		summary['total_error'] = "ERROR:  {}/{} = {}%".format(num_error, num_jobs, percent(num_error, num_jobs))
	else:
		summary['total_error'] = False

	return summary


def generate_html_file(htmlcode, remind=False, owner=''):
	''' generates HTML file from given HTML code
		if generating file for reminder, owner should be passed as well
	'''
	try:
		os.makedirs('archive')
	except FileExistsError:
		pass
	owner = owner.split('@')[0]
	reportType = 'reminder_for_{}'.format(owner) if remind else 'report'
	filename = './archive/{}_{:%Y-%m-%d_%H-%M-%S}.html'.format(
		reportType,
		datetime.datetime.now()
	)
	with open(filename, 'w') as file:
		file.write(htmlcode)
	return filename


def percent(part, whole):
	''' basic percent function
	'''
	if whole == 0:
		return 0
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
