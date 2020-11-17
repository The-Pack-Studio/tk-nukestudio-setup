# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import re
import os
import sys
import traceback

# from PySide import QtCore
from sgtk.platform.qt import QtCore

from tank.platform import Application

from tank import TankError

import hiero.ui
import hiero.core



class setupNukestudio(Application):
    def init_app(self):

        self.setProjectRoots_onNewProject_Callback()
        hiero.core.ApplicationSettings().setValue("ocioConfigFile", self.setOCIO())


    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.
        """
        return True




    def setOCIO(self):


        tk = self.sgtk
        root = tk.roots['secondary']

        ocio_template = self.get_template("ocio_template")
        OCIOPath = self.sgtk.paths_from_template(ocio_template, {})[0]

        if not os.path.isfile(OCIOPath):
            self.log_debug("No %s file on disk" % OCIOPath)
            return None

        OCIOConfig = OCIOPath.replace("\\", '/')
        self.log_debug("OOOOOOOOOOOOOOOOOocio is : %s" % OCIOConfig)
        return OCIOConfig

    def setProjectRoots_onNewProject_Callback(self):
        
        def secondaryProject(event):

            for p in hiero.core.projects():
                osNewPath = None
                if sys.platform == "darwin":
                    if p.exportRootDirectory().startswith("//sledge/vol1/Projects") :
                        osNewPath = p.exportRootDirectory().replace("//sledge/vol1/Projects", "/Volumes/vol1/Projects")
                elif sys.platform == "win32":
                    if p.exportRootDirectory().startswith("/mnt/sledge/Projects") :
                        osNewPath = p.exportRootDirectory().replace("/Volumes/vol1/Projects", "//sledge/vol1/Projects")

                if osNewPath :
                    print "tk-hiero-export path replacement ", p.exportRootDirectory() ," -> ", osNewPath
                    p.setCustomExportDirectory(osNewPath)

                if p.exportRootDirectory() == self.tank.project_path  or not p.exportRootDirectory() or p.exportRootDirectory() == "c:" :
                    print "tk-hiero-export path auto setting ", self.sgtk.roots["secondary"]
                    p.setCustomExportDirectory(self.sgtk.roots["secondary"])
        
                p.setUseCustomExportDirectory(True)

        hiero.core.events.registerInterest('kAfterNewProjectCreated', secondaryProject)
        hiero.core.events.registerInterest('kAfterProjectLoad', secondaryProject)
