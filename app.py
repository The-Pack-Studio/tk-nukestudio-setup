from __future__ import print_function
import re
import os
import sys
import traceback

import PySide2.QtWidgets as QtWidgets
from sgtk.platform.qt import QtCore

from tank.platform import Application

from tank import TankError

import hiero.ui
import hiero.core



class setupNukestudio(Application):

    def init_app(self):

        self.shotgun_project_fps = self._get_shotgun_project_fps()
        self.ocio_config = self._get_ocio_config()

        if self.ocio_config:
            hiero.core.ApplicationSettings().setValue("ocioConfigFile", self.ocio_config) # NS preferences

        hiero.core.events.registerInterest('kAfterNewProjectCreated', self.setExportRoot)
        hiero.core.events.registerInterest('kAfterProjectLoad', self.setExportRoot)
        hiero.core.events.registerInterest('kAfterNewProjectCreated', self.set_default_sequence_framerate)
        hiero.core.events.registerInterest('kAfterProjectLoad', self.set_default_sequence_framerate)

        hiero.core.events.registerInterest('kAfterProjectLoad', self.set_ocio_config)

    def destroy_app(self):
        self.log_debug("Destroying tk-nukestudio-setup app")
        
        # remove any callbacks that were registered by the handler:
        hiero.core.events.unregisterInterest('kAfterNewProjectCreated', self.setExportRoot)
        hiero.core.events.unregisterInterest('kAfterProjectLoad', self.setExportRoot)
        hiero.core.events.unregisterInterest('kAfterNewProjectCreated', self.set_default_sequence_framerate)
        hiero.core.events.unregisterInterest('kAfterProjectLoad', self.set_default_sequence_framerate)


    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.
        """
        return False


    def _get_ocio_config(self):

        tk = self.sgtk
        root = tk.roots['secondary']

        ocio_template = self.get_template("ocio_template")
        OCIOPath = self.sgtk.paths_from_template(ocio_template, {})[0]

        if not os.path.isfile(OCIOPath):
            self.log_debug("No %s file on disk" % OCIOPath)
            return None

        OCIOConfig = OCIOPath.replace(os.path.sep, '/')
        return OCIOConfig


    def set_ocio_config(self, event):

        project = event.project
        current_ocio_config = project.ocioConfigPath()
        if current_ocio_config:
            if current_ocio_config != self.ocio_config:

                msgBox = QtWidgets.QMessageBox()
                msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                msgBox.setWindowTitle("Project Settings : OCIO config problem")
                msgBox.setText("Ocio config for this project is:\n{}\n\nIt should be:\n{}\n\n Please correct this in the project settings".format(current_ocio_config, self.ocio_config))
                msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)

                msgBox.exec_()

  
    def setExportRoot(self, event):

        project = event.project

        # Always use the CustomExportDirectory
        project.setUseCustomExportDirectory(True)

        exportPath = project.exportRootDirectory()
        newExportPath = self._path_conversion(exportPath)

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
       

    def set_default_sequence_framerate(self, event):
        '''
        Compares the frame rate of the shotgun project (see overview page of the project in SG)
        with the default sequence frame rate in the NukeStudio project
        for new projects, silently sets the default frame rate to shotgun's framerate
        for existing projects, compares and warns user to allow him to correct the framerate
        '''

        project = event.project
        current_nukestudio_fps = project.framerate() # returns either integer or float

        shotgun_project_fps = self.shotgun_project_fps
        if not shotgun_project_fps: # Shotgun project framerate is not defined, skip
            return None

        if event.type == "kAfterNewProjectCreated":
            project.setFramerate(shotgun_project_fps)

        if event.type == "kAfterProjectLoad":

            if str(current_nukestudio_fps) == "Invalid":
                project.setFramerate(shotgun_project_fps)

            elif current_nukestudio_fps != shotgun_project_fps:

                msgBox = QtWidgets.QMessageBox()
                msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                msgBox.setWindowTitle("Project Settings : Frame rate problem")
                msgBox.setText("Default sequence frame rate is {}fps.\nFrame rate for this Shotgun project ({}) is {}fps.\nChange default frame rate of sequences ?\n\nNote : This will only affect new sequences.\nExisting sequences will not be modified".format(current_nukestudio_fps, self.context.project['name'], shotgun_project_fps))

                change_button = msgBox.addButton("Change to {}fps".format(shotgun_project_fps), QtWidgets.QMessageBox.AcceptRole)
                cancel_button = msgBox.addButton("Keep {}fps".format(current_nukestudio_fps), QtWidgets.QMessageBox.RejectRole)

                msgBox.exec_()
                if msgBox.clickedButton() == change_button:
                    project.setFramerate(shotgun_project_fps)
                    self.log_debug("Changing the default seq framerate from {} to {}".format(current_nukestudio_fps, shotgun_project_fps))
                    print ('change_button')
                if msgBox.clickedButton() == cancel_button:
                    pass

 
    def _path_conversion(self, path):

        if sys.platform.startswith("win32"):
            path = path.replace("/Volumes/vol1/Projects", "//sledge/vol1/Projects")
            path = path.replace("/mnt/vol1/Projects", "//sledge/vol1/Projects")
            path = path.replace("Y:/Projects", "//sledge/vol1/Projects")

        elif sys.platform.startswith("darwin"):
            path = path.replace("//sledge/vol1/Projects", "/Volumes/vol1/Projects")
            path = path.replace("//Sledge/vol1/Projects", "/Volumes/vol1/Projects")
            path = path.replace("Y:/Projects", "/Volumes/vol1/Projects")

            path = path.replace("/mnt/vol1/Projects", "/Volumes/vol1/Projects")

        elif sys.platform.startswith("linux"):
            path = path.replace("//sledge/vol1/Projects", "/mnt/vol1/Projects")
            path = path.replace("//Sledge/vol1/Projects", "/mnt/vol1/Projects")
            path = path.replace("Y:/Projects", "/mnt/vol1/Projects")

            path = path.replace("/Volumes/vol1/Projects", "/mnt/vol1/Projects")

        return path

    def _get_shotgun_project_fps(self):

        tk = self.sgtk
        shotgun_project = self.context.project

        sg_filters = [['id', 'is', shotgun_project['id']]]
        fields = ["sg_projectfps"]
        data = tk.shotgun.find_one('Project', filters=sg_filters, fields=fields)

        shotgun_project_fps = data.get('sg_projectfps')

        if not shotgun_project_fps: # if not found, do nothing
            return None

        return shotgun_project_fps
