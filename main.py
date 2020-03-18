#!/usr/bin/python3

import os
import re
import sys
import yaml
import jinja2
import jenkins
import argparse
import bugzilla
import datetime
from jira import JIRA

from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

os.environ['PYTHONHTTPSVERIFY'] = '0'
all_bugs = []
all_tickets = []


def get_jira_dict(ticket_ids):
    ''' takes in set of ticket_ids and returns dictionary with
        ticket_ids as keys and API data as values
    '''

    # initialize ticket list
    tickets = {}

    # Initialize connection
    auth = (config['jira_username'], config['jira_password'])
    options = {
        "server": config['jira_url'],
        "verify": config['certificate']
    }
    jira = JIRA(auth=auth, options=options)

    # iterate through ticket ids from blocker file
    for ticket_id in ticket_ids:

        # 0 should be default in YAML file (i.e. no tickers recorded)
        # if there is a 0 entry then that should be the only "ticket", so break
        if ticket_id == 0:
            tickets[0] = {'ticket_name': 'No ticket on file', 'ticket_url': None}
            continue

        # otherwise record real ticket in overall list
        all_tickets.append(ticket_id)

        # get ticket info from jira API
        try:
            issue = jira.issue(ticket_id)
            ticket_name = issue.fields.summary
        except Exception as e:
            print("Jira API Call Error: ", e)
            ticket_name = ticket_id
        finally:
            ticket_url = config['jira_url'] + "/browse/" + str(ticket_id)
            tickets[ticket_id] = {
                'ticket_name': ticket_name,
                'ticket_url': ticket_url
            }
    jira.close()

    return tickets


def generate_header(user, job_search_fields):
    user_properties = user['property']
    user_email_address = [prop['address'] for prop in user_properties if prop['_class'] == 'hudson.tasks.Mailer$UserProperty'][0]
    date = '{:%m/%d/%Y at %I:%M%p %Z}'.format(datetime.datetime.now())
    header = {
        'user_email_address': user_email_address,
        'date': date,
        'job_search_fields': job_search_fields
    }
    return header


def get_jenkins_jobs(server, job_search_fields):

    # parse list of search fields
    fields = job_search_fields.split(',')

    # fetch all jobs from server
    all_jobs = server.get_jobs()

    # parse out all jobs that do not contain any search field and/or are not OSP10, OSP13, OSP15 or OSP16 jobs
    relevant_jobs = []
    for job in all_jobs:
        if ('10' not in job['name']) and ('13' not in job['name']) and ('15' not in job['name']) and ('16' not in job['name']):
            continue
        else:
            for field in fields:
                if field in job['name']:
                    relevant_jobs.append(job)
                    break

    return relevant_jobs


def get_bugs_dict(bug_ids):
    ''' takes in set of bug_ids and returns dictionary with
        bug_ids as keys and API data as values
    '''

    # initialize bug dictionary
    bugs = {}

    # iterate through bug ids from set
    for bug_id in bug_ids:

        # 0 should be default in YAML file (i.e. no bugs recorded)
        # if present reference should be made in bug dict
        if bug_id == 0:
            bugs[0] = {'bug_name': 'No bug on file', 'bug_url': None}
            continue

        # get bug info from bugzilla API
        try:

            # hotfix: API call does not work if '/' present at end of URL string
            parsed_bz_url = config['bz_url'].rstrip('/')

            bz_api = bugzilla.Bugzilla(parsed_bz_url)
            bug = bz_api.getbug(bug_id)
            bug_name = bug.summary
        except Exception as e:
            print("Bugzilla API Call Error: ", e)
            bug_name = "BZ#" + str(bug_id)
        finally:
            bug_url = config['bz_url'] + "/show_bug.cgi?id=" + str(bug_id)
            bugs[bug_id] = {'bug_name': bug_name, 'bug_url': bug_url}

    return bugs


def get_bugs_set(blockers):
    ''' Takes in blockers object and generates a set of all unique bug ids
        including 0 if it is present
    '''
    bug_list = []
    for job in blockers:
        bz = blockers[job]['bz']
        if bz != [0]:
            all_bugs.extend(bz)
        bug_list.extend(bz)

    return set(bug_list)


def get_jira_set(blockers):
    ''' Takes in blockers object and generates a set of all unique jira-ticket ids
        including 0 if it is present
    '''
    jira_list = []
    for job in blockers:
        jira = blockers[job]['jira']
        if jira != [0]:
            all_tickets.extend(jira)
        jira_list.extend(jira)

    return set(jira_list)


def get_osp_version(job_name):
    version = re.search(r'\d+', job_name)
    if version is None:
        return None
    else:
        return version.group()


def percent(part, whole):
    return round(100 * float(part) / float(whole), 1)


# main script execution
if __name__ == '__main__':

    # argument parsing
    parser = argparse.ArgumentParser(description='An automated report generator for Jenkins CI')
    parser.add_argument("--config", default="config.yaml", type=str, help="Configuration YAML file to use")
    parser.add_argument("--blockers", default="blockers.yaml", type=str, help="Blockers YAML file to use")
    parser.add_argument("--test", default=False, action='store_true', help="Flag to send email to test address")
    args = parser.parse_args()
    config_file = args.config
    blocker_file = args.blockers
    test = args.test

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

    # Get set from the list of all bugs in all jobs
    all_bugs_set = get_bugs_set(blockers) if blockers else {}

    # Create dictionary the set of all bugs (key) with name and link as value
    all_bugs_dict = get_bugs_dict(all_bugs_set)

    # Get set from the list of all jira-tickets in all jobs
    all_tickets_set = get_jira_set(blockers) if blockers else {}

    # Create dictionary from the set of all jira tickets with ticket id as key and name and link as value
    all_jira_dict = get_jira_dict(all_tickets_set)

    # connect to jenkins server
    try:
        server = jenkins.Jenkins(config['jenkins_url'], username=config['jenkins_username'], password=config['jenkins_api_token'])
        user = server.get_whoami()
    except Exception as e:
        print("Error connecting to Jenkins server: ", e)
        sys.exit()

    # generate report header
    header = generate_header(user, config['job_search_fields'])

    # fetch all relevant jobs
    jobs = get_jenkins_jobs(server, config['job_search_fields'])

    # exit if no jobs found
    num_jobs = len(jobs)
    if num_jobs == 0:
        print("No jobs found with given search field. Exiting...")
        sys.exit()

    # iterate through all relevant jobs and build report rows
    num_success = 0
    num_unstable = 0
    num_failure = 0
    num_error = 0
    rows = []
    for job in jobs[::-1]:
        job_name = job['name']
        osp_version = get_osp_version(job_name)

        # skip if no OSP version could be found
        if osp_version is None:
            print('No OSP version could be found in job {}. Skipping...'.format(job_name))
            continue

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

            compose = [action['text'][13:-4] for action in build_actions if 'core_puddle' in action.get('text', '')][0]
            lcb_url = build_info['url']
            lcb_result = build_info['result']
        except Exception as e:
            print("Jenkins API call error: ", e)
            continue

        # take action based on last completed build result
        if lcb_result == "SUCCESS":
            num_success += 1
            bugs = [{'bug_name': 'N/A', 'bug_url': None}]
            tickets = [{'ticket_name': 'N/A', 'ticket_url': None}]
        elif lcb_result == "UNSTABLE":
            num_unstable += 1

            # get all related bugs to job
            try:
                bug_ids = blockers[job_name]['bz']
                bugs = list(map(all_bugs_dict.get, bug_ids))
            except:
                bugs = [{'bug_name': "Could not find relevant bug", 'bug_url': None}]

            # get all related tickets to job
            try:
                ticket_ids = blockers[job_name]['jira']
                tickets = list(map(all_jira_dict.get, ticket_ids))
            except:
                tickets = [{'ticket_name': "Could not find relevant ticket", 'ticket_url': None}]

        elif lcb_result == "FAILURE":
            num_failure += 1

            # get all related bugs to job
            try:
                bug_ids = blockers[job_name]['bz']
                bugs = list(map(all_bugs_dict.get, bug_ids))
            except:
                bugs = [{'bug_name': "Could not find relevant bug", 'bug_url': None}]

            # get all related tickets to job
            try:
                ticket_ids = blockers[job_name]['jira']
                tickets = list(map(all_jira_dict.get, ticket_ids))

            except:
                tickets = [{'ticket_name': "Could not find relevant ticket", 'ticket_url': None}]

        else:
            lcb_result = "ERROR"
            num_error += 1
            bugs = [{'bug_name': 'N/A', 'bug_url': None}]
            tickets = [{'ticket_name': 'N/A', 'ticket_url': None}]

        # build row
        row = {
            'osp_version': osp_version,
            'job_name': job_name,
            'job_url': job_url,
            'lcb_num': lcb_num,
            'lcb_url': lcb_url,
            'compose': compose,
            'lcb_result': lcb_result,
            'bugs': bugs,
            'tickets': tickets,
        }

        # append row to rows
        rows.append(row)

    # sort rows by descending OSP version
    rows = sorted(rows, key=lambda row: row['osp_version'], reverse=True)

    # calculate summary
    summary = {}

    # job result metrics
    summary['total_success'] = "Total SUCCESS:  {}/{} = {}%".format(num_success, num_jobs, percent(num_success, num_jobs))
    summary['total_unstable'] = "Total UNSTABLE: {}/{} = {}%".format(num_unstable, num_jobs, percent(num_unstable, num_jobs))
    summary['total_failure'] = "Total FAILURE:  {}/{} = {}%".format(num_failure, num_jobs, percent(num_failure, num_jobs))

    # bug metrics
    if len(all_bugs) == 0:
        summary['total_bugs'] = "Blocker Bugs: 0 total"
    else:
        unique_bugs = set(all_bugs)
        summary['total_bugs'] = "Blocker Bugs: {} total, {} unique".format(len(all_bugs), len(unique_bugs))

    # ticket metrics
    if len(all_tickets) == 0:
        summary['total_tickets'] = "Blocker Tickets: 0 total"
    else:
        unique_tickets = set(all_tickets)
        summary['total_tickets'] = "Blocker Tickets: {} total, {} unique".format(len(all_tickets), len(unique_tickets))

    # include error report if needed
    if num_error > 0:
        summary['total_error'] = "Total ERROR:  {}/{} = {}%".format(num_error, num_jobs, percent(num_error, num_jobs))
    else:
        summary['total_error'] = False

    # initialize jinja2 vars
    loader = jinja2.FileSystemLoader('./template.html')
    env = jinja2.Environment(loader=loader)
    template = env.get_template('')

    # generate HTML report
    htmlcode = template.render(
        header=header,
        rows=rows,
        summary=summary
    )

    # construct email
    msg = MIMEMultipart()
    msg['From'] = header['user_email_address']
    msg['Subject'] = config['email_subject']
    if test:
        msg['To'] = config['email_to_test']
    else:
        msg['To'] = config['email_to']
    msg.attach(MIMEText(htmlcode, 'html'))

    # create SMTP session - if jeeves is unable to do so an HTML file will be generated
    try:
        with SMTP(config['smtp_host']) as smtp:

            # start TLS for security
            smtp.starttls()

            # use ehlo or helo if needed
            smtp.ehlo_or_helo_if_needed()

            # send email
            smtp.sendmail(msg["From"], msg["To"], msg.as_string())

    except:
        with open("report.html", "w") as file:
            print("Error sending email report - HTML file generated")
            file.write(htmlcode)
