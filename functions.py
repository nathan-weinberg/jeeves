''' Shared library of functions for other Python files
'''
import os
import re
import datetime
import bugzilla
from jira import JIRA


def generate_header(user, source, remind=False):
	''' generates header
		if remind is true, header source should be blocker_file
		if remind is false, header source should be job_search_fields
	'''
	user_properties = user['property']
	user_email_address = [prop['address'] for prop in user_properties if prop['_class'] == 'hudson.tasks.Mailer$UserProperty'][0]
	date = '{:%m/%d/%Y at %I:%M%p %Z}'.format(datetime.datetime.now())

	# show only filename in remind header, not full path
	if remind:
		source = source.rsplit('/', 1)[-1]

	header = {
		'user_email_address': user_email_address,
		'date': date,
		'source': source
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


def get_bugs_dict(bug_ids, config):
	''' takes in set of bug_ids and returns dictionary with
		bug_ids as keys and API data as values
	'''

	# initialize bug dictionary
	bugs = {}

	# API connection does not work if '/' present at end of URL string
	parsed_bz_url = config['bz_url'].rstrip('/')
	bz_api = None

	# iterate through bug ids from set
	for bug_id in bug_ids:

		# 0 should be default in YAML file (i.e. no bugs recorded)
		# if present reference should be made in bug dict
		if bug_id == 0:
			bugs[0] = {'bug_name': 'No bug on file', 'bug_url': None}
			continue

		# get bug info from bugzilla API
		try:

			# initialize connection if it has not yet been done (either first iteration or previously failed)
			if bz_api is None:
				bz_api = bugzilla.Bugzilla(parsed_bz_url)

			bug = bz_api.getbug(bug_id)
			bug_status = '[' + bug.status + ']'
			bug_summary = bug.summary
			bug_name = ' '.join([bug_status, bug_summary])
		except Exception as e:
			print("Bugzilla API Call Error: ", e)
			bug_name = "BZ#" + str(bug_id)
			bz_api = None
		finally:
			bug_url = config['bz_url'] + "/show_bug.cgi?id=" + str(bug_id)
			bugs[bug_id] = {'bug_name': bug_name, 'bug_url': bug_url}

	return bugs


def get_bugs_set(blockers):
	''' takes in blockers object and generates a set of all unique bug ids
		including 0 if it is present
	'''
	bug_set = set()
	for job in blockers:

		# try to fetch 'bz' field from job
		try:
			bz = blockers[job]['bz']
			bug_set.update(bz)

		# failure means data was not formatted correctly for given job - log and skip
		except Exception as e:
			print("Error getting bug IDs from blockers file for job {}: {}".format(job, e))
			continue

	return bug_set


def get_jenkins_job_info(server, job_name):
	''' takes in jenkins server object and job name
		returns dict of API info for given job if success
		returns False if failure
	'''

	# set default value for job_info for cased exception handling
	job_info = {}

	try:
		job_info = server.get_job_info(job_name)
		job_url = job_info['url']
		lcb_num = job_info['lastCompletedBuild']['number']
		build_info = server.get_build_info(job_name, lcb_num)
		build_actions = build_info['actions']
		build_parameters = [action['parameters'] for action in build_actions if action.get('_class') == 'hudson.model.ParametersAction'][0]
		run_mode = [action['text'] for action in build_actions if 'RUN_MODE: periodic' in action.get('text', '')]
		gerrit_patch = [param['value'] for param in build_parameters if 'GERRIT_CHANGE_URL' in param.get('name', '')]

		# find most recent build where the following is NOT true
		# build has label "RUN MODE: periodic"
		# build is associated with a gerrit patch (i.e. GERRIT_CHANGE_URL is present)
		while run_mode != [] or gerrit_patch != []:
			lcb_num = lcb_num - 1
			build_info = server.get_build_info(job_name, lcb_num)
			build_actions = build_info['actions']
			build_parameters = [action['parameters'] for action in build_actions if action.get('_class') == 'hudson.model.ParametersAction'][0]
			run_mode = [action['text'] for action in build_actions if 'RUN_MODE: periodic' in action.get('text', '')]
			gerrit_patch = [param['value'] for param in build_parameters if 'GERRIT_CHANGE_URL' in param.get('name', '')]

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
		if job_info.get('builds') == []:
			lcb_num = None
			lcb_url = None
			compose = "N/A"
			lcb_result = "NO_KNOWN_BUILDS"

		# Unknown error, skip job
		else:
			print("Jenkins API call error on job {}: {} - skipping...".format(job_name, e))
			return False

	jenkins_api_info = {
		'job_url': job_url,
		'lcb_num': lcb_num,
		'lcb_url': lcb_url,
		'compose': compose,
		'lcb_result': lcb_result,
	}
	return jenkins_api_info


def get_jenkins_jobs(server, job_search_fields):
	''' takes in a Jenkins server object and job_search_fields string
		returns list of jobs with given search field as part of their name
	'''

	# parse list of search fields
	fields = job_search_fields.split(',')
	fields_length = len(fields)

	# remove spacing from strings
	for i in range(fields_length):
		fields[i] = fields[i].strip(' ')

	# fetch all jobs from server
	all_jobs = server.get_jobs()

	# parse out all jobs that do not contain any search field and/or are not OSP10, OSP13, OSP15 or OSP16 jobs
	relevant_jobs = []
	supported_versions = ['10', '13', '15', '16', '16.1']
	for job in all_jobs:
		job_name = job['name']
		if any(supported_version in job_name for supported_version in supported_versions):
			for field in fields:
				if field in job_name:
					relevant_jobs.append(job)
					break

	return relevant_jobs


def get_jira_dict(ticket_ids, config):
	''' takes in set of ticket_ids and returns dictionary with
		ticket_ids as keys and API data as values
	'''

	# initialize ticket dictionary
	tickets = {}

	# initialize jira variable and config options
	auth = (config['jira_username'], config['jira_password'])
	options = {
		"server": config['jira_url'],
		"verify": config['certificate']
	}
	jira = None

	# iterate through ticket ids from set
	for ticket_id in ticket_ids:

		# 0 should be default in YAML file (i.e. no tickers recorded)
		# if there is a 0 entry then that should be the only "ticket", so break
		if ticket_id == 0:
			tickets[0] = {'ticket_name': 'No ticket on file', 'ticket_url': None}
			continue

		# get ticket info from jira API
		try:

			# initialize connection if it has not yet been done (either first iteration or previously failed)
			if jira is None:
				jira = JIRA(auth=auth, options=options)

			issue = jira.issue(ticket_id)
			ticket_status = '[' + str(issue.fields.status) + ']'
			ticket_summary = issue.fields.summary
			ticket_name = ' '.join([ticket_status.upper(), ticket_summary])
		except Exception as e:
			print("Jira API Call Error: ", e)
			ticket_name = ticket_id
			jira = None
		finally:
			ticket_url = config['jira_url'] + "/browse/" + str(ticket_id)
			tickets[ticket_id] = {
				'ticket_name': ticket_name,
				'ticket_url': ticket_url
			}

	# close Jira connection if open
	if jira is not None:
		jira.close()

	return tickets


def get_jira_set(blockers):
	''' takes in blockers object and generates a set of all unique jira ticket ids
		including 0 if it is present
	'''
	jira_set = set()
	for job in blockers:

		# try to fetch 'jira' field from job
		try:
			jira = blockers[job]['jira']
			jira_set.update(jira)

		# failure means data was not formatted correctly for given job - log and skip
		except Exception as e:
			print("Error getting jira IDs from blockers file for job {}: {}".format(job, e))
			continue

	return jira_set


def get_osp_version(job_name):
	''' gets osp version from job name via regex
		returns None if no version is found
	'''
	version = re.search(r'\d+\.*\d*', job_name)
	if version is None:
		return None
	return version.group()


def get_other_blockers(blockers, job_name):
	''' takes in blockers object and job name
		returns list of 'other' blockers
	'''

	other_blockers = blockers[job_name]['other']
	other = []
	for blocker in other_blockers:
		other.append({'other_name': blocker.get('name', 'Link'), 'other_url': blocker.get('url', None)})
	return other


def has_blockers(blockers, job_name):
	''' returns True if job_name in blockers has any defined blockers
		returns False otherwise
	'''
	is_bz = blockers[job_name].get('bz', [0])
	is_jira = blockers[job_name].get('jira', [0])
	is_other = blockers[job_name].get('other', [0])
	if (is_bz == [0]) and (is_jira == [0]) and (is_other == [0]):
		return False
	return True


def percent(part, whole):
	''' basic percent function
	'''
	return round(100 * float(part) / float(whole), 1)


def validate_config(config):
	''' validates config fields
		raises exception if required field is not present
	'''
	required_fields = [
		'jenkins_url',
		'jenkins_username',
		'jenkins_api_token',
		'job_search_fields',
		'bz_url',
		'jira_url',
		'jira_username',
		'jira_password',
		'certificate',
		'smtp_host',
		'email_subject',
		'email_to'
	]
	for field in required_fields:
		if config.get(field) is None:
			raise Exception('field "{}" is not defined'.format(field))
	return None
