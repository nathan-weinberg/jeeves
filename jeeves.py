#!/usr/bin/python3

import os
import sys
import yaml
import jenkins
import argparse
import datetime

from report import run_report
from remind import run_remind

os.environ['PYTHONHTTPSVERIFY'] = '0'


def generate_report_header(user, job_search_fields):
	''' generates header for report
	'''
	user_properties = user['property']
	user_email_address = [prop['address'] for prop in user_properties if prop['_class'] == 'hudson.tasks.Mailer$UserProperty'][0]
	date = '{:%m/%d/%Y at %I:%M%p %Z}'.format(datetime.datetime.now())
	header = {
		'user_email_address': user_email_address,
		'date': date,
		'job_search_fields': job_search_fields
	}
	return header


def generate_remind_header(user, blocker_file):
	''' generates header for reminder
	'''
	user_properties = user['property']
	user_email_address = [prop['address'] for prop in user_properties if prop['_class'] == 'hudson.tasks.Mailer$UserProperty'][0]
	date = '{:%m/%d/%Y at %I:%M%p %Z}'.format(datetime.datetime.now())
	header = {
		'user_email_address': user_email_address,
		'date': date,
		'blocker_file': blocker_file
	}
	return header


# main script execution
if __name__ == '__main__':

	# argument parsing
	parser = argparse.ArgumentParser(description='An automated report generator for Jenkins CI')
	parser.add_argument("--config", default="config.yaml", type=str, help='Configuration YAML file to use')
	parser.add_argument("--blockers", default="blockers.yaml", type=str, help='Blockers YAML file to use')
	parser.add_argument("--test", default=False, action='store_true', help='Flag to send email to test address')
	parser.add_argument("--save", default=False, action='store_true', help='Flag to save report to archives')
	parser.add_argument("--remind", default=False, action='store_true', help='Flag to run Jeeves in "reminder" mode. Note this will override --test and --save')
	args = parser.parse_args()
	config_file = args.config
	blocker_file = args.blockers
	test = args.test
	save = args.save
	remind_flag = args.remind

	# load configuration data
	try:
		with open(config_file, 'r') as file:
			config = yaml.safe_load(file)
	except Exception as e:
		print("Error loading configuration data: ", e)
		sys.exit()

	# load blocker data
	try:
		with open(blocker_file, 'r') as file:
			blockers = yaml.safe_load(file)
	except Exception as e:
		print("Error loading blocker configuration data: ", e)
		sys.exit()

	# connect to jenkins server
	try:
		server = jenkins.Jenkins(config['jenkins_url'], username=config['jenkins_username'], password=config['jenkins_api_token'])
		user = server.get_whoami()
	except Exception as e:
		print("Error connecting to Jenkins server: ", e)
		sys.exit()

	# execute Jeeves in either 'remind' or 'report' mode
	if remind_flag:
		header = generate_remind_header(user, blocker_file)
		run_remind(config, blockers, server, header)
	else:
		header = generate_report_header(user, config['job_search_fields'])
		run_report(config, blockers, server, header, test, save)
