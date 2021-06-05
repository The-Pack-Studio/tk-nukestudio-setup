from __future__ import print_function
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

        hiero.core.ApplicationSettings().setValue("ocioConfigFile", self.setOCIO())
        hiero.core.events.registerInterest('kAfterNewProjectCreated', self.setExportRoot)
        hiero.core.events.registerInterest('kAfterProjectLoad', self.setExportRoot)
    
    def destroy_app(self):
        self.log_debug("Destroying tk-nukestudio-setup app")
        
        # remove any callbacks that were registered by the handler:
        hiero.core.events.unregisterInterest('kAfterNewProjectCreated', self.setExportRoot)
        hiero.core.events.unregisterInterest('kAfterProjectLoad', self.setExportRoot)



    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.
        """
        return False


    def setOCIO(self):

        tk = self.sgtk
        root = tk.roots['secondary']

        ocio_template = self.get_template("ocio_template")
        OCIOPath = self.sgtk.paths_from_template(ocio_template, {})[0]

        if not os.path.isfile(OCIOPath):
            self.log_debug("No %s file on disk" % OCIOPath)
            return None

        OCIOConfig = OCIOPath.replace(os.path.sep, '/')
        self.log_debug("Setting Ocio to : %s" % OCIOConfig)
        return OCIOConfig

  
    def setExportRoot(self, event):

        project = event.project

        # Always use the CustomExportDirectory
        project.setUseCustomExportDirectory(True)

        exportPath = project.exportRootDirectory()
        newExportPath = exportPath

        if sys.platform.startswith("win32"):
            newExportPath = newExportPath.replace("/Volumes/vol1/Projects", "//sledge/vol1/Projects")
            newExportPath = newExportPath.replace("/mnt/vol1/Projects", "//sledge/vol1/Projects")
            newExportPath = newExportPath.replace("Y:/Projects", "//sledge/vol1/Projects")

        elif sys.platform.startswith("darwin"):
            newExportPath = newExportPath.replace("//sledge/vol1/Projects", "/Volumes/vol1/Projects")
            newExportPath = newExportPath.replace("//Sledge/vol1/Projects", "/Volumes/vol1/Projects")
            newExportPath = newExportPath.replace("Y:/Projects", "/Volumes/vol1/Projects")

            newExportPath = newExportPath.replace("/mnt/vol1/Projects", "/Volumes/vol1/Projects")

        elif sys.platform.startswith("linux"):
            newExportPath = newExportPath.replace("//sledge/vol1/Projects", "/mnt/vol1/Projects")
            newExportPath = newExportPath.replace("//Sledge/vol1/Projects", "/mnt/vol1/Projects")
            newExportPath = newExportPath.replace("Y:/Projects", "/mnt/vol1/Projects")

            newExportPath = newExportPath.replace("/Volumes/vol1/Projects", "/mnt/vol1/Projects")


        if newExportPath != exportPath :
            self.log_debug("Replacing the original exportRootDirectory value from %s to %s" % (exportPath, newExportPath))
            project.setCustomExportDirectory(newExportPath)

        # the tk-nukestudio engine sets the exportRootDirectory to tank.project_path,
        # tank.project_path = \\server01\shared2\projects\xxxxxxxxx,
        # so we replace it
        if project.exportRootDirectory() == self.tank.project_path  or not project.exportRootDirectory() or project.exportRootDirectory() == "c:":
            exportPath = self.sgtk.roots["secondary"]
            exportPath = exportPath.replace(os.path.sep, "/")

            self.log_debug("Setting the exportRootDirectory to %s" % exportPath)
            project.setCustomExportDirectory(exportPath)

        


