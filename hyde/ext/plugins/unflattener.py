
# -*- coding: utf-8 -*-
"""
Plugins related to folders and paths
"""

from hyde.plugin import Plugin
from hyde.fs import Folder

import re
import os

class UnflattenerPlugin(Plugin):
    """
    The plugin class for creating nested folders. 
    """

    def __init__(self, site):
        super(UnflattenerPlugin, self).__init__(site)

    def begin_site(self): 
        """
        Finds all the resources that need to be unflattened and changes the
        relative deploy path of all resources in those folders
        """
        items = []
        try:
            items = self.site.config.unflattener.folders
        except AttributeError:
            pass

        self.logger.debug(items)
        for item in items:
            self.logger.debug(item)
            node = None
            target = ''
            try:
                node = self.site.content.node_from_relative_path(item)
            except AttributeError:
                continue
            if node:
                for resource in node.walk_resources():
                    if hasattr(resource, 'meta') and hasattr(resource.meta, 'date'):
                        date = resource.meta.date
                        self.logger.debug(resource.meta.date)

                        #pattern = re.compile('()-()-()')
                        #date = pattern.match(date)
                        #target_path = os.path.join(date.year, date.month, date.day) 
                        #target_path = date.strftime("%Y/%m/%d/")
                        target_path = "%s/%d/%d/%d/%s" % (node.name, date.year, date.month, date.day, resource.name)
                        self.logger.debug('Unflattening resource with date [%s] to path [%s]' % (date, target_path)) 
                        resource.relative_deploy_path = target_path
