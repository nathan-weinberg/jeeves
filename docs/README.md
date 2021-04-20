# Jeeves
![flake8](https://github.com/nathan-weinberg/jeeves/workflows/flake8/badge.svg)
![pytest](https://github.com/nathan-weinberg/jeeves/workflows/pytest/badge.svg)
[![codecov](https://codecov.io/gh/nathan-weinberg/jeeves/branch/master/graph/badge.svg)](https://codecov.io/gh/nathan-weinberg/jeeves)

## Purpose
Jeeves is an automated report generator for Jenkins CI. It generates an HTML report using Jinja2 templating and sends it out over email using Python's smtplib.

## Setup
Create a file named `config.yaml` based off `config.yaml.example` with the following fields filled in:
- **jenkins_url**: URL of your Jenkins server
- **job_search_fields**: Filter of Jenkins Jobs to included in report, e.g. DFG-ceph-rhos. To search for multiple fields, seperate them by comma, e.g. DFG-ceph-rhos,DFG-all-unified. Allows for regex searches as well, e.g. ^DFG-ceph,rgw$
- **filter_param_name**: Optional field that instructs Jeeves to skip any build that lacks the corresponding value of the given build parameter. Must be used on in conjunction with **filter_param_value**
- **filter_param_value**: Optional field that instructs Jeeves to skip any build that lacks this value for the corresponding build parameter name. Must be used in conjunction with **filter_param_name**
- **bz_url**: URL of your Bugzilla, e.g. https://bugzilla.redhat.com/
- **jira_url**: URL of your Jira, e.g. https://projects.engineering.redhat.com/
- **jira_username**: Your Jira username
- **jira_password**: Your Jira password
- **certificate**: CRT file to authenticate with Jira server
- **smtp_host**: SMTP host of your email
- **email_subject**: Subject of your email report
- **email_from**: The email address of the sender
- **email_to**: Email address you would like to send your report to. To send the report to multiple emails, seperate them by comma, e.g. recipient1@website1.com,recipient2@website2.org
- **email_to_test**: Email address to send test reports to (note: this field is only required if you run Jeeves with the `--test-email` flag)
- **stage_logs**: Optional dict field that instructs Jeeves how to build URLs to a log files for a corresponding failed build stage
- **supported_versions**: Optional list that instructs Jeeves which osp versions are supported and should
appear in the report

If you wish to use a different configuration file, you can specify it as a command line argument.

#### Tracking Blockers
Create a file named `blockers.yaml` based off `blockers.yaml.example` with each UNSTABLE and FAILED job containing two sections - 'bz' and 'jira' - and a list of the blocker IDs. 0 indicates blocker bug/ticket is not on file (either doesn't exist or hasn't been created yet).

If you have a blocker for a job that is neither a Bugzilla bug or a Jira ticket, you may add a section to your blockers file called 'other', with each item having two fields - 'name' and 'url'. Both fields are optional - you can include one, the other, or both.

If you wish to use a different blockers file, you can specify it as a command line argument.

#### Tracking Owners
You can define "owners" for a job in `blockers.yaml` for use with reminder mode. To do so, simply add an "owners" subfield to a job with one or more emails. You can see some examples of this in `blockers.yaml.example`.

## Usage
`$ ./jeeves.py [-h] [--config CONFIG] [--blockers BLOCKERS] [--preamble PREAMBLE] [--template TEMPLATE] [--mode {report,remind}] [--no-email] [--test-email]`

For a base run, simply run `$ ./jeeves.py` using the `--config` and `--blocker` flags if needed as detailed above. For details on the additional flags avaliable see below:
- To add a "preamble" to the report, add `--preamble <preamble file>`. The file should be written in HTML.
    - This flag will be ignored if Jeeves is run in "reminder" mode
- To use a different template for the report, add `--template <template file>`.  The template should be in the templates directory.
    - This flag will be ignored if Jeeves is run in "reminder" mode
- To change which run mode Jeeves will use, add `--mode` along with the run mode you wish to use
    - Note that running Jeeves in "remind" mode will override the usage of both the `--no-email` flag and the `--test-email` flag
- To only save report to the 'archive' folder, and not send an email, add `--no-email`
- To send report to email specified in `email_to_test` field, add `--test-email`
	- Note that running Jeeves with the `--test-email` flag will not save the report to 'archive' folder
	- As such, running Jeeves with both the `--test-email` and `--no-email` flags will result in no report being saved and no email being sent

#### Filtering Builds
By setting values in `config.yaml` for both **filter_param_name** and **filter_param_value**, Jeeves will automically skip any Jenkins builds that lack the given build parameter and value and search for the next latest completed build. Note that this is done by decrementing the build number Jeeves searches for until a build with the given parameter and value is found. Make sure your Jenkins jobs have a linear build history without missing builds if you intend to use this feature.

If you don't wish to use this feature, simply omit the two fields from your `config.yaml` file and Jeeves will simply use the last completed build for a given job.

#### Reminder Mode
Jeeves has a reminder mode that will send an email to "owners" of jobs in Jenkins that have "UNSTABLE" or "FAILURE" status. You can add as many "owners" as you would like to a given job. You can see some examples of this in `blockers.yaml.example` 

#### Failed Stage Logs
Jeeves has an option to add URLs to a report which point to one of more log files for a corresponding failed build stage. Log files are mapped to the stage based on the `stage_logs` dict defined in `config.yaml`. In 
`config.yaml.example` you can find some stages already mapped to logs files. Use it as a reference on how to map logs to your reports. A single stage can be mapped to single or multiple log files. It is not required to map all stages from a job to log files. Jeeves will skip adding URLs to stages which are not defined in the `stage_logs`.

### Packages
- [PyYAML](https://pyyaml.org/) for parsing config YAML
- [Jinja2](https://jinja.palletsprojects.com/en/2.10.x/) for generating HTML
- [Python Jenkins](https://python-jenkins.readthedocs.io/en/latest/) for interacting with Jenkins
- [python-bugzilla](https://github.com/python-bugzilla/python-bugzilla) for interacting with Bugzilla
- [jira-python](https://jira.readthedocs.io/en/master/index.html) for interacting with Jira

To install packages run:

`$ pip install -r requirements.txt`

It is recommended you do this within a virtual environment.

## Linting
Jeeves follows a set of [PEP8](https://www.python.org/dev/peps/pep-0008/) standards in the interest of code clarity and consistency. These rules are enforced with the [flake8](https://flake8.pycqa.org/en/latest/) library. Configuration for linting resides in the `.flake8.ini` file.

To run linting simply run the `flake8` command within the Jeeves directory.

## Testing
Jeeves has a small but growing test suite driven by [pytest](https://docs.pytest.org/en/latest/index.html). Currently all tests reside in the `tests` directory.

To run tests simply run the `pytest` command within the Jeeves directory.

## Contributing
Please see contribution guidelines in [CONTRIBUTING.md](CONTRIBUTING.md)

## Notes
Jeeves was designed for use by Red Hat OpenStack QE and the organization's production CI environment - while the project can be used for other Jenkins environments, it may require some tweaking to work as expected.
