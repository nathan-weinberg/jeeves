from jeeves.blockers import *


def test_get_bugs_dict():
	pass


def test_get_bugs_set():
	mockers = {
		'job1': {'bz': [0]},
		'job2': {'bz': [123456]},
		'job3': {'bz': [123456, 789123]}
	}
	assert get_bugs_set(mockers) == {123456, 789123}


def test_get_tickets_dict():
	pass


def test_get_tickets_set():
	mockers = {
		'job1': {'jira': [0]},
		'job2': {'jira': ['RHOSINFRA-123']},
		'job3': {'jira': ['RHOSINFRA-123', 'RHOSENTDFG-456']}
	}
	assert get_tickets_set(mockers) == {'RHOSINFRA-123', 'RHOSENTDFG-456'}


def test_get_other_blockers():
	pass


def test_has_blockers():
	mockers = {
		'job1': {'bz': [123456]},
		'job2': {'jira': ['RHOSINFRA-123']},
		'job3': {'other': {'name': 'this is a test name'}},
		'job4': {'bz': [0]},
		'job5': {'jira': [0]},
		'job6': {'other': [0]},
		'job7': {'owners': 'foo@bar.com'},
		'job8': {'owners': 'foo@bar.com', 'bz': [123456], 'jira': ['RHOSINFRA-123']},
		'job9': {}
	}
	assert has_blockers(mockers, 'job1') == True
	assert has_blockers(mockers, 'job2') == True
	assert has_blockers(mockers, 'job3') == True
	assert has_blockers(mockers, 'job4') == False
	assert has_blockers(mockers, 'job5') == False
	assert has_blockers(mockers, 'job6') == False
	assert has_blockers(mockers, 'job7') == False
	assert has_blockers(mockers, 'job8') == True
	assert has_blockers(mockers, 'job9') == False
