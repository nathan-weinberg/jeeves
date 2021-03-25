# library functions for handling job data

import re
import datetime


def get_stage_failure(build_stages):
	''' takes in build stages dict
		returns string with the name of failed stage or 'N/A if there is no failed stage
	'''
	for stage in build_stages['stages']:
		if stage['status'] == 'FAILED':
			return stage.get('name', 'N/A')
	return 'N/A'


def get_jenkins_job_info(server, job_name, filter_param_name=None, filter_param_value=None):
	''' takes in jenkins server object and job name
		optionally takes name and value of jenkins param to filter builds by
		returns dict of API info for given job if success
		returns False if failure
	'''

	# set default value for job_info for cased exception handling
	job_info = {}

	try:
		job_info = server.get_job_info(job_name)
		job_url = job_info['url']
		lcb_num = job_info['lastCompletedBuild']['number']
		tempest_tests_failed = None
		stage_failure = 'N/A'
		build_info = server.get_build_info(job_name, lcb_num)
		if build_info['result'] == 'FAILURE' or build_info['result'] == 'UNSTABLE':
			build_stages = server.get_build_stages(job_name, lcb_num)
			stage_failure = get_stage_failure(build_stages)

		build_actions = build_info['actions']
		for action in build_actions:
			if action.get('_class') in ['com.tikal.jenkins.plugins.multijob.MultiJobParametersAction', 'hudson.model.ParametersAction']:
				build_parameters = action['parameters']
			elif action.get('_class') == 'hudson.tasks.junit.TestResultAction':
				tempest_tests_failed = action['failCount']

		# if desired, get last completed build with custom parameter and value
		if filter_param_name is not None and filter_param_value is not None:
			api_param_value = [param['value'] for param in build_parameters if filter_param_name == param.get('name', '')][0]
			while api_param_value != filter_param_value:
				lcb_num = lcb_num - 1
				build_info = server.get_build_info(job_name, lcb_num)
				build_actions = build_info['actions']
				for action in build_actions:
					if action.get('_class') in ['com.tikal.jenkins.plugins.multijob.MultiJobParametersAction', 'hudson.model.ParametersAction']:
						build_parameters = action['parameters']
						break
				api_param_value = [param['value'] for param in build_parameters if filter_param_name == param.get('name', '')][0]

		build_time = build_info.get('timestamp')
		build_days_ago = (datetime.datetime.now() - datetime.datetime.fromtimestamp(build_time / 1000)).days
		lcb_url = build_info['url']
		lcb_result = build_info['result']
		composes = [str(action['html']).split('core_puddle:')[1].split('<')[0].strip() for action in build_actions if 'core_puddle' in action.get('html', '')]

		# No composes could be found; likely a failed job where the 'core_puddle' var was never calculated
		if composes == []:
			compose = "Could not find compose"
			second_compose = None
		# Two composes found - job is likely Update or Upgrade
		elif len(composes) == 2:
			compose = composes[0]
			second_compose = composes[1]
		# One compose found
		else:
			compose = composes[0]
			second_compose = None

	except Exception as e:

		# No "Last Completed Build" found
		# Checks for len <= 1 as running builds are included in the below query
		if len(job_info.get('builds')) <= 1:
			lcb_num = None
			lcb_url = None
			compose = "N/A"
			second_compose = None
			build_days_ago = "N/A"
			lcb_result = "NO_KNOWN_BUILDS"
			stage_failure = 'N/A'
			tempest_tests_failed = None

		# Unknown error, skip job
		else:
			print("Jenkins API call error on job {}: {} - skipping...".format(job_name, e))
			return False

	jenkins_api_info = {
		'job_url': job_url,
		'lcb_num': lcb_num,
		'lcb_url': lcb_url,
		'compose': compose,
		'second_compose': second_compose,
		'lcb_result': lcb_result,
		'build_days_ago': build_days_ago,
		'tempest_tests_failed': tempest_tests_failed,
		'stage_failure': stage_failure
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

	# check for fields that contain valid regex
	relevant_jobs = []
	supported_versions = ['13', '16.1', '16.2']
	for field in fields:
		try:

			# fetch all jobs from server that match the given regex or search
			all_jobs = server.get_job_info_regex(field)

			# parse out all jobs that do not contain any search field and/or are not a supported version
			for job in all_jobs:
				job_name = job['name']
				if any(supported_version in job_name for supported_version in supported_versions):
					relevant_jobs.append(job)

		except Exception as e:
			print("Error compiling regex: {} - skipping this search field...".format(e))

	return relevant_jobs


def get_osp_version(job_name):
	''' gets osp version from job name via regex
		if multiple versions detected, the highest number is considered osp version
		returns osp version as a string or None if no version is found
	'''
	versions = re.findall(r'1{1}[0,3,6]{1}\.{1}\d{1}|1{1}[0,3,6]{1}(?=\D+)', job_name)
	if not versions:
		return None
	versions_f = map(float, versions)
	max_value = max(versions_f)
	return '{:g}'.format(max_value)
