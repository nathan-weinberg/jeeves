#!/usr/bin/python3

import os
import sys
import yaml
import jenkins
import argparse

from report import run_report
from remind import run_remind
from functions import generate_header, validate_config

os.environ['PYTHONHTTPSVERIFY'] = '0'


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

	# load configuration data - if YAML format is invalid, log and end program execution
	try:
		with open(config_file, 'r') as file:
			config = yaml.safe_load(file)
			validate_config(config)
	except Exception as e:
		print("Error loading configuration data: ", e)
		sys.exit()

	# load blocker data - if YAML format is invalid, log and end program execution
	try:
		with open(blocker_file, 'r') as file:
			blockers = yaml.safe_load(file)
	except Exception as e:
		print("Error loading blocker configuration data: ", e)
		sys.exit()

	# connect to jenkins server - if not possible, log and end program execution
	try:
		server = jenkins.Jenkins(config['jenkins_url'], username=config['jenkins_username'], password=config['jenkins_api_token'])
		user = server.get_whoami()
	except Exception as e:
		print("Error connecting to Jenkins server: ", e)
		sys.exit()

	# execute Jeeves in either 'remind' or 'report' mode
	# if remind, header source should be blocker_file
	# if report, header source should be job_search_fields
	if remind_flag:
		header = generate_header(user, blocker_file, remind=True)
		run_remind(config, blockers, server, header)
	else:
		header = generate_header(user, config['job_search_fields'])
		run_report(config, blockers, server, header, test, save)
