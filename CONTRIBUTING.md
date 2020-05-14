# Contributing to Jeeves

Thank you for your interest in contributing to Jeeves!

## Getting Started
Every contributor must do the following before getting started:

1. **Become a Jeeves Collaborator:** Only GitHub Collaborators in the Jeeves repo can submit code, so if you aren't already, reach out to [Nathan Weinberg](mailto:nweinber@redhat.com) to recieve an invite giving you the appropriate permissions.

2. **Fork the Jeeves repo:** All work being done **must** be done within your own fork on a working branch (i.e. not `master`). To submit your work, make a Pull Request from your fork's working branch to the `master` branch of the main repo (more on this below). **Do not** push branches directly to the main repo for the project; they will be deleted without consultation.

3. **Clone your fork to your local machine:** Navigate to your fork of Jeeves and clone it as follows:

```bash
$ git clone git@github.com:<your-github-username>/jeeves.git
``` 

4. **Set your remotes properly:** Make sure your remotes are set such that `git remote -v` gives you an output similar to the following:

``` bash
origin		git@github.com:<your-github-username>/jeeves.git (fetch)
origin		git@github.com:<your-github-username>/jeeves.git (push)
upstream	git@github.com:nathan-weinberg/jeeves.git (fetch)
upstream	git@github.com:nathan-weinberg/jeeves.git (push)
```

To add the `upstream` repo, run the following command:

`$ git remote add upstream git@github.com:nathan-weinberg/jeeves.git`

## Making your change
Now that you've setup your permissions, fork, and remotes properly, it's time to start making your change! Ensure you do the following before you begin to code:

1. **Ensure there is an associated GitHub Issue with the work you are going to do:** All Pull Requests made **must** be associated with an issue; if one does not already exist for the change you are making please create one, assign it to yourself, and tag it with the approporate labels.

2. **Ensure your working branch is up-to-date:** Before creating your working branch, you must ensure it is up-to-date with the latest changes in the main repo's `master` branch. It is recommended you do so in the following way:

``` bash
[jeeves]$ git checkout master				# checkout your master branch
[jeeves]$ git pull upstream master			# update your local master branch with latest changes from upstream
[jeeves]$ git push origin master			# update your remote master branch with latest changes
[jeeves]$ git checkout -b <working-branch>		# create your new working branch containing latest changes
```

## Submitting your change via making a Pull Request
Before you make a Pull Request, make sure you do the following:

1. **Test your code:** Make sure you test your code **thouroughly** before submitting; the higher quality a Pull Request is submitted the shorter the review process will be :) 

2. **Lint your code:** Jeeves has its own set of styling guidelines enforced by `flake8`; you can run these locally with the following commands:

```bash
[jeeves]$ flake8 --ignore=E117,E501,E722,W191 jeeves.py
[jeeves]$ flake8 --ignore=E117,E501,E722,W191 report.py
[jeeves]$ flake8 --ignore=E117,E501,E722,W191 remind.py
[jeeves]$ flake8 --ignore=E117,E501,E722,W191 functions.py
```

3. **Sqaush your commits:** In most cases, only one commit per Pull Request will be allowed. Make sure not to submit Pull Requests with multiple commits unless you've consulted with an admin. If you're not sure how to squash commits, there are several guides online with directions on how to do so.

Once you've done all this, make your Pull Request from your fork's working branch to the `master` branch of the main repo and make sure to reference the related issue in either the commit message or Pull Request description.

## Updating a Pull Request
If changes were requested on your Pull Request, update it in the following way to ensure consistency:

1. Make the requested changes locally
2. Readd the relevant files
3. Run `$ git commit --amend` to amend the commit with the requested changes
4. Run `$ git push -f origin <your-working-branch>` to update the Pull Request

Happy contributing!
