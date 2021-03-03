# library functions for handling blocker data

import bugzilla
from jira import JIRA


def get_bugs_dict(bug_ids, config):
	''' takes in set of bug_ids and returns dictionary with
		bug_ids as keys and API data as values
		a bug_id value of 0 will be ignored
	'''

	# initialize bug dictionary
	bug_dict = {}

	# API connection does not work if '/' present at end of URL string
	parsed_bz_url = config['bz_url'].rstrip('/')
	bz_api = None

	# iterate through bug ids from set
	for bug_id in bug_ids:

		# a bug_id value of 0 is used as a placeholder, not a valid bug
		# skip as there is no API data to be fetched in this case
		if bug_id == 0:
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
			bug_dict[bug_id] = {'bug_name': bug_name, 'bug_url': bug_url}

	return bug_dict


def get_bugs_set(blockers):
	''' takes in blockers dict and generates a set of all unique bug ids
		excludes 0 if it is present
		passing an empty dict will result in an empty set
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

	# discard bug_id value of 0 from set if present as this is not a valid bug
	bug_set.discard(0)
	return bug_set


def get_tickets_dict(ticket_ids, config):
	''' takes in set of ticket_ids and returns dictionary with
		ticket_ids as keys and API data as values
		a ticket_id with a value of 0 will be ignored
	'''

	# initialize ticket dictionary
	ticket_dict = {}

	# initialize jira variable and config options
	auth = (config['jira_username'], config['jira_password'])
	options = {
		"server": config['jira_url'],
		"verify": config['certificate']
	}
	jira = None

	# iterate through ticket ids from set
	for ticket_id in ticket_ids:

		# a ticket_id value of 0 is used as a placeholder, not a valid ticket
		# skip as there is no API data to be fetched in this case
		if ticket_id == 0:
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
			ticket_dict[ticket_id] = {
				'ticket_name': ticket_name,
				'ticket_url': ticket_url
			}

	# close Jira connection if open
	if jira is not None:
		jira.close()

	return ticket_dict


def get_tickets_set(blockers):
	''' takes in blockers object and generates a set of all unique jira ticket ids
		excluding 0 if it is present
		passing an empty dict will result in an empty set
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

	# discard ticket_id value of 0 from set if present as this is not a valid ticket
	jira_set.discard(0)
	return jira_set


def get_other_blockers(blockers, job_name):
	''' takes in blockers object and job name
		returns list of 'other' blockers
	'''
	other = []
	other_blockers = blockers[job_name].get('other')
	if other_blockers is None:
		return other
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
