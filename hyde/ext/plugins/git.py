# -*- coding: utf-8 -*-

"""
Contains classes and utilities to extract information from git repository
"""
from hyde.fs import File, Folder
from hyde.plugin import Plugin


import subprocess
import traceback

import os
import re
import json
import dateutil.parser 

from operator import attrgetter

class GitTrackerPlugin(Plugin):
    """
    Track changes across a repository and display it in a useful way. 
    """
    # For all resources
    # If it's trackable by git, and we want it to be tracked
    # Look at the relevant changesets 
    # And generate an uhh...a JSON file, possibly, or something else sophisticated.
    def __init__(self, site):
        super(GitTrackerPlugin, self).__init__(site)

    def parser(self, lines):
        commit_hash = re.search(r" (\w+)", lines[0]).group(1)   # commit <hash>
        author_name, email = re.search(r"Author: (.*) <(.*)>", lines[1]).group(1, 2)
        matched_date = re.search(r"Date:\s+(\w.*$)", lines[2]).group(1) 
        date  = dateutil.parser.parse(matched_date)
       
        commit_msg = []
        for idx, l in enumerate(lines[4:]): 
            if not re.match(r"diff --git", l):
                commit_msg.append(l)
            else:
                diff = lines[4+idx:] 
                break

        to_utf8 = lambda x: unicode(x, "utf8")

        # make sure to encode to utf8
        commit_msg = to_utf8('\n'.join(commit_msg)) 
        diff = to_utf8('\n'.join(diff[:-1]).strip()) 
        

        commit = {
                "hash": commit_hash,
                "author": author_name,
                "email": email,
                "date": date,
                "msg": commit_msg,
                "diff": diff
                }

        return commit



    def begin_site(self):
        """
        Initialize plugin. Retrieve changesets from git
        """
        
        valid_extensions = getattr(self.site.config.gittracker, 'extensions', ['html'])

        for node in self.site.content.walk():
            for resource in node.resources:
                if os.path.splitext(resource.path)[1].lstrip(".") not in valid_extensions:  
                    continue

                try:
                    exclude = resource.meta.exclude
                    if exclude:
                        continue
                except AttributeError:
                    pass

                try:
                    track = resource.meta.track
                except AttributeError:
                    continue


                resource_commits = [] 

                if track == True:
                    self.logger.debug("Checking commits on [%s]" % resource)
                    args = ["git", "log", "--no-decorate", "-p", "--word-diff=plain", "-z", resource.path]
                    try:
                        commits = subprocess.check_output(args).split('\0')
                    except subprocess.CalledProcessError:
                        self.logger.warning("Unable to get git commit history for [%s]" % resource)
                        continue

                    if len(commits) < 2:
                        self.logger.info("No git history for [%s]" % resource)
                        continue

                    for c in commits:
                        lines = [x.strip() for x in c.split('\n')]
                        commit_p = self.parser(lines)
                        resource_commits.append(commit_p)

                    resource.meta.commits = resource_commits
                    self.logger.info("Added %d commits on for [%s]" % (len(resource_commits), resource))

class GitDatesPlugin(Plugin):
    """
    Extract creation and last modification date from git and include
    them in the meta data if they are set to "git". Creation date
    is put in `created` and last modification date in `modified`.
    """

    def __init__(self, site):
        super(GitDatesPlugin, self).__init__(site)

    def begin_site(self):
        """
        Initialize plugin. Retrieve dates from git
        """
        for node in self.site.content.walk():
            for resource in node.resources:
                created = None
                modified = None
                try:
                    created = resource.meta.created
                except AttributeError:
                    pass
                try:
                    modified = resource.meta.modified
                except AttributeError:
                    pass
                # Everything is already overrided
                if created != "git" or modified != "git":
                    continue
                # Run git log --pretty=%ai
                try:
                    commits = subprocess.check_output(["git", "log", "--pretty=%ai",
                                                       resource.path]).split("\n")

                except subprocess.CalledProcessError:
                    self.logger.warning("Unable to get git history for [%s]" % resource)
                    continue
                commits = commits[:-1]
                if not commits:
                    self.logger.info("No git history for [%s]" % resource)
                    continue
                if created == "git":
                    created = dateutil.parser.parse(commits[-1].strip())
                    resource.meta.created = created
                if modified == "git":
                    modified = dateutil.parser.parse(commits[0].strip())
                    resource.meta.modified = modified
