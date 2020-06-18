# Jeeves
![](https://github.com/nathan-weinberg/jeeves/workflows/flake8/badge.svg)
![](https://github.com/nathan-weinberg/jeeves/workflows/pytest/badge.svg)

## Purpose
Jeeves is an automated report generator for Jenkins CI. It generates an HTML report using Jinja2 templating and sends it out over email using Python's smtplib.

## Setup
Create a file named "config.yaml" based off "config.yaml.example" with the following fields filled in:
- **jenkins_url**: URL of your Jenkins server
- **jenkins_username**: Your Jenkins username
- **jenkins_api_token**: Your Jenkins API token
- **job_search_fields**: Filter of Jenkins Jobs to included in report, e.g. DFG-ceph-rhos. To search for multiple fields, seperate them by comma, e.g. DFG-ceph-rhos,DFG-all-unified
- **bz_url**: URL of your Bugzilla, e.g. https://bugzilla.redhat.com/
- **jira_url**: URL of your Jira, e.g. https://projects.engineering.redhat.com/
- **jira_username**: Your Jira username
- **jira_password**: Your Jira password
- **certificate**: CRT file to authenticate with Jira server
- **smtp_host**: SMTP host of your email
- **email_subject**: Subject of your email report
- **email_to**: Email address you would like to send your report to. To send the report to multiple emails, seperate them by comma, e.g. recipient1@website1.com,recipient2@website2.org
- **email_to_test**: Email address to send test reports to (note: this field is only required if you run Jeeves with the `--test` flag)

If you wish to use a different configuration file, you can specify it as a command line argument.

#### Tracking Blockers
Create a file named "blockers.yaml" based off "blockers.yaml.example" with each UNSTABLE and FAILED job containing two sections - 'bz' and 'jira' - and a list of the blocker IDs. 0 indicates blocker bug/ticket is not on file (either doesn't exist or hasn't been created yet)

If you have a blocker for a job that is neither a Bugzilla bug or a Jira ticket, you may add a section to your blockers file called 'other', with each item having two fields - 'name' and 'url'. Both fields are optional - you can include one, the other, or both.

If you wish to use a different blockers file, you can specify it as a command line argument.

#### Tracking Owners
You can define "owners" for a job in "blockers.yaml" for use with reminder mode. To do so, simply add an "owners" subfield to a job with one or more emails. You can see some examples of this in "blockers.yaml.example". 

## Usage
To run:
- `$ ./jeeves.py [-h] [--config CONFIG] [--blockers BLOCKERS] [--no-email] [--test] [--remind]`
- To only save report to the 'archive' folder, and not send an email, add `--no-email`
- To send report to email specified in `email_to_test` field, add `--test`
	- Note that running Jeeves with the `--test` flag will not save the report to 'archive' folder
	- As such, running Jeeves with both the `--test` and `--no-email` flags will result in no report being saved and no email being sent
- To run Jeeves in "reminder" mode, add `--remind`
    - Note this will override the usage of both `--no-email` and `--test`

#### Reminder Mode
Jeeves has a reminder mode that will send an email to "owners" of jobs in Jenkins that have "UNSTABLE" or "FAILURE" status. You can add as many "owners" as you would like to a given job. You can see some examples of this in "blockers.yaml.example". 

### Packages
- [PyYAML](https://pyyaml.org/) for parsing config YAML
- [Jinja2](https://jinja.palletsprojects.com/en/2.10.x/) for generating HTML
- [Python Jenkins](https://python-jenkins.readthedocs.io/en/latest/) for interacting with Jenkins
- [python-bugzilla](https://github.com/python-bugzilla/python-bugzilla) for interacting with Bugzilla
- [jira-python](https://jira.readthedocs.io/en/master/index.html) for interacting with Jira

To install packages run:

`$ pip install -r requirements.txt`

It is recommended you do this within a virtual environment.

## Testing
Jeeves has a small but growing test suite driven by [pytest](https://docs.pytest.org/en/latest/index.html). Currently all tests reside in the `test_functions.py` file.

To run tests simply run the `pytest` command within the Jeeves directory.

## Contributing
Please see contribution guidelines in [CONTRIBUTING.md](CONTRIBUTING.md)

## Notes
Jeeves was designed for use by Red Hat OpenStack QE and the organization's production CI environment - while the project can be used for other Jenkins environments, it may require some tweaking to work as expected.
