# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2020 Richard Frangenberg
#
# Licensed under GNU GPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.

from ntpath import basename
import os,sys
import shutil
import subprocess
import logging 
import time

# logging.basicConfig(level=logging.INFO)
try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

if sys.version[0] == "3":
    pVersion = 3
else:
    pVersion = 2

try:
    import P4
except:
    modulePath = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "external_modules/p4_api{}".format(pVersion))
    if not modulePath in sys.path:
        sys.path.append(modulePath)
    import P4

import P4Publish

logger = logging.getLogger(__name__)

class P4Connection:
    connected = "Connected"
    disconnected = "Disconnected"

def get_logger(logger_name,create_file=False, log_file="logfile.log"):

    # create logger for prd_ci
    log = logging.getLogger(logger_name)
    log.setLevel(level=logging.INFO)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if create_file:
            # create file handler for logger.
        if not os.path.exists(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file))
        fh = logging.FileHandler(log_file)
        fh.setLevel(level=logging.DEBUG)
        fh.setFormatter(formatter)
        log.addHandler(fh)
    # reate console handler for logger.
    ch = logging.StreamHandler()
    ch.setLevel(level=logging.DEBUG)
    ch.setFormatter(formatter)

    log.addHandler(ch)
    return   log 
class Prism_Perforce_Functions(object):
    CONNECTED, DISCONNECTED = "P4 Connected", "P4 Disconnected"

    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.p4 = P4.P4()
        self.logger = get_logger(__name__, True, os.path.join(os.path.dirname(core.prismIni), "perforce_logging.log"))

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True

    @err_catcher(name=__name__)
    def prismSettings_loadUI(self, origin):

        origin.gb_p4PrjIntegration = QGroupBox("Perforce Settings:")
        origin.w_Perforce = QWidget()
        lo_p4I = QHBoxLayout()
        lo_p4I.addWidget(origin.w_Perforce)
        origin.gb_p4PrjIntegration.setLayout(lo_p4I)
        origin.gb_p4PrjIntegration.setCheckable(True)
        origin.gb_p4PrjIntegration.setChecked(False)

        lo_p4 = QGridLayout()
        origin.w_Perforce.setLayout(lo_p4)

        origin.l_p4Exec = QLabel("Perforce Executable:")
        origin.l_p4Site = QLabel("Perforce Port:")
        origin.l_p4PrjName = QLabel("Project Name:")
        origin.l_p4UserName = QLabel("User Name:")
        origin.l_p4WorkspaceName = QLabel("Workspace Name:")
        origin.l_p4Passwd = QLabel("User Password:")
        origin.l_p4Connection = QLabel("")
        origin.e_p4exec = QLineEdit()
        origin.e_p4port = QLineEdit()
        origin.e_p4PrjName = QLineEdit()
        origin.e_p4UserName = QLineEdit()
        origin.e_p4UserPassword = QLineEdit()
        origin.e_p4userworkspacename = QLineEdit()
        origin.e_p4templateworkspacename = QLineEdit()
        origin.e_p4defaultmapping = QTextEdit()
        origin.e_p4defaultstream = QLineEdit()

        origin.bt_p4testconnection = QPushButton("Test Connection")
        origin.bt_p4testconnection.setMinimumHeight(50)
        origin.e_p4UserPassword.setEchoMode(QLineEdit.PasswordEchoOnEdit)

        lo_p4.addWidget(origin.l_p4Site)
        lo_p4.addWidget(origin.l_p4PrjName)
        lo_p4.addWidget(origin.l_p4UserName)
        lo_p4.addWidget(origin.l_p4Passwd)
        lo_p4.addWidget(origin.l_p4WorkspaceName)
        lo_p4.addWidget(origin.l_p4Exec)
        lo_p4.addWidget(origin.l_p4Connection)
        lo_p4.addWidget(origin.e_p4port, 0, 1)
        lo_p4.addWidget(origin.e_p4PrjName, 1, 1)
        lo_p4.addWidget(origin.e_p4UserName, 2, 1)
        lo_p4.addWidget(origin.e_p4UserPassword, 3, 1)
        lo_p4.addWidget(origin.e_p4userworkspacename, 4, 1)
        lo_p4.addWidget(origin.e_p4exec, 5, 1)
        lo_p4.addWidget(origin.bt_p4testconnection, 6, 1)

        origin.w_prjSettings.layout().insertWidget(5, origin.gb_p4PrjIntegration)
        origin.groupboxes.append(origin.gb_p4PrjIntegration)

        origin.gb_p4PrjIntegration.toggled.connect(
            lambda x: self.prismSettings_p4Toggled(origin, x)
        )
        origin.bt_p4testconnection.clicked.connect(
            lambda x: self.connectToPerforce(show_message=True)
        )

    @err_catcher(name=__name__)
    def prismSettings_p4Toggled(self, origin, checked):
        origin.w_Perforce.setVisible(checked)

    @err_catcher(name=__name__)
    def prismSettings_loadSettings(self, origin, settings):
        if "perforce" in settings:
            if "p4username" in settings["perforce"]:
                origin.e_p4UserName.setText(settings["perforce"]["p4username"])
            elif os.getenv("P4_USER"):
                origin.e_p4UserName.setText(os.getenv("P4_USER"))
            else:
                origin.e_p4UserName.setText(self.p4.user)

            if "p4userpassword" in settings["perforce"]:
                origin.e_p4UserPassword.setText(settings["perforce"]["p4userpassword"])
            elif os.getenv("P4_PASSWORD"):
                origin.e_p4UserPassword.setText(os.getenv("P4_PASSWORD"))
            else:
                origin.e_p4UserPassword.setText(self.p4.password)

            if "p4userworkspacename" in settings["perforce"]:
                origin.e_p4userworkspacename.setText(settings["perforce"]["p4userworkspacename"])
            elif os.getenv("P4_CLIENT"):
                origin.e_p4userworkspacename.setText(os.getenv("P4_CLIENT"))
            else:
                origin.e_p4userworkspacename.setText(self.p4.client)

            if "p4userworkspaceroot" in settings["perforce"]:
                origin.e_p4userworkspaceroot.setText(settings["perforce"]["p4userworkspaceroot"])
            elif os.getenv("P4_ROOT"):
                origin.e_p4userworkspaceroot.setText(os.getenv("P4_ROOT"))
            else:
                try:
                    self.connectToPerforce(show_message=False)
                    origin.e_p4userworkspaceroot.setText(self.p4.fetch_client(self.p4.client).get("Root", ""))
                except:
                    pass

    @err_catcher(name=__name__)
    def prismSettings_loadPrjSettings(self, origin, settings):
        if "perforce" in settings:
            if "active" in settings["perforce"]:
                origin.gb_p4PrjIntegration.setChecked(settings["perforce"]["active"])

            if not "installpath" in settings["perforce"]:
                settings["perforce"]["installpath"] = r"C:\ProgramFiles\Perforce"

            origin.e_p4exec.setText(settings["perforce"]["installpath"])

            if "port" in settings["perforce"]:
                origin.e_p4port.setText(settings["perforce"]["port"])
            elif os.getenv("P4_PORT"):
                origin.e_p4port.setText(os.getenv("P4_PORT"))
            else:
                origin.e_p4port.setText(self.p4.port)

            if "defaultusername" in settings["perforce"]:
                if not origin.e_p4UserName.text():
                    origin.e_p4UserName.setText(settings["perforce"]["defaultusername"])
            elif os.getenv("P4_USER"):
                origin.e_p4UserName.setText(os.getenv("P4_USER"))

            if "projectname" in settings["perforce"]:
                origin.e_p4PrjName.setText(settings["perforce"]["projectname"])

        # self.prismSettings_spToggled(origin, origin.gb_p4PrjIntegration.isChecked())

    @err_catcher(name=__name__)
    def prismSettings_saveSettings(self, origin, settings):
        if "perforce" not in settings:
            settings["perforce"] = {}

        # settings["perforce"]["p4useaccount"] = origin.gb_p4Account.text()
        if origin.e_p4UserName.text():
            settings["perforce"]["p4username"] = origin.e_p4UserName.text()
        if origin.e_p4UserPassword.text():
            settings["perforce"]["p4userpassword"] = origin.e_p4UserPassword.text()
        if origin.e_p4userworkspacename.text():
            settings["perforce"]["p4userworkspacename"] = origin.e_p4userworkspacename.text()
        # settings["perforce"]["p4userworkspaceroot"] = origin.e_p4UserPassword.text()

    @err_catcher(name=__name__)
    def prismSettings_savePrjSettings(self, origin, settings):
        if "perforce" not in settings:
            settings["perforce"] = {}

        settings["perforce"]["active"] = origin.gb_p4PrjIntegration.isChecked()
        settings["perforce"]["installpath"] = origin.e_p4exec.text()
        settings["perforce"]["port"] = origin.e_p4port.text()
        settings["perforce"]["projectname"] = origin.e_p4PrjName.text()

    # the following function are called by Prism at specific events, which are indicated by the function names
    # you can add your own code to any of these functions.
    @err_catcher(name=__name__)
    def onProjectCreated(self, origin, projectPath, projectName):
        pass

    @err_catcher(name=__name__)
    def onProjectChanged(self, origin):
        pass

    @err_catcher(name=__name__)
    def onSetProjectStartup(self, origin):
        pass

    @err_catcher(name=__name__)
    def projectBrowser_loadUI(self, origin):
        pass


    @property
    def connectStatusWidget(self):
        if not hasattr(self, "_connected_widget"):
            self._connected_widget = QCheckBox(Prism_Perforce_Functions.DISCONNECTED)
            # self._connected_widget.disable()
            self._connected_widget.setAutoFillBackground(True);
            self._connected_widget.toggled.connect( lambda state: self.connectToPerforce())
            self._connected_widget.setStyleSheet("background-color:yellow; color:black")
        return self._connected_widget
    
    @connectStatusWidget.setter
    def connectStatusWidget(self, value):
        self._connected_widget.setChecked(value)
        if value:
            self._connected_widget.setText(Prism_Perforce_Functions.CONNECTED)
            self._connected_widget.setStyleSheet("background-color:green; color:white")
        else:
            self._connected_widget.setText(Prism_Perforce_Functions.DISCONNECTED)
            self._connected_widget.setStyleSheet("background-color:yellow; color:black")
        return self._connected_widget 

    @err_catcher(name=__name__)
    def onProjectBrowserStartup(self, origin):
        if not origin.statusBar():
            origin.setStatusBar(QStatusBar())
        origin.statusBar().addWidget(self.connectStatusWidget)

    @err_catcher(name=__name__)
    def onProjectBrowserClose(self, origin):
        pass

    @err_catcher(name=__name__)
    def onPrismSettingsOpen(self, origin):
        pass

    @err_catcher(name=__name__)
    def onPrismSettingsSave(self, origin):
        pass

    @err_catcher(name=__name__)
    def onStateManagerOpen(self, origin):
        pass

    @err_catcher(name=__name__)
    def onStateManagerClose(self, origin):
        pass

    @err_catcher(name=__name__)
    def onSelectTaskOpen(self, origin):
        pass

    @err_catcher(name=__name__)
    def onStateCreated(self, origin, state, stateData):
        if not self.isPluginActive():
            return
        self.chb_createInPerforce = QGroupBox("Perforce")
        self.chb_createInPerforce.setCheckable(True)
        self.chb_createInPerforce.setLayout(QVBoxLayout())
        self.chb_createInPerforce.setChecked(True)
        
        p4path = ""
        data = self.core.entities.getScenefileData(self.core.getCurrentFileName())
        entity_path = self.core.getEntityBasePath(data.get("filename"))
        category = data.get("category")
        state_layout = None

        p4edit_wid = None

        state_type = "undefined"
        taskname = "undefined"
        fileformat = ".undefined"

        if hasattr(state, "cb_outType") and hasattr(state, "gb_export"):
            state_type = "export"
            state_layout = state.gb_export.layout()
            taskname = state.l_taskName.text()
            fileformat = state.cb_outType.currentText()
            state.cb_outType.currentTextChanged.connect(lambda x: self.setP4StateExport(origin, state, stateData))
            self.lb_PerforceExportPath = QLabel("Perforce Export Path:")
            self.le_PerforceExportPath = QLineEdit()
            self.chb_createInPerforce.layout().addWidget(self.lb_PerforceExportPath)    
            self.chb_createInPerforce.layout().addWidget(self.le_PerforceExportPath)
            self.le_PerforceExportPath.editingFinished.connect(lambda x: self.setP4StateExport(origin, state, stateData, x))
            # self.setP4StateExport(origin, state, stateData)
        elif hasattr(state, "gb_import"):
            state_type = "import"
            state_layout = state.gb_import.layout()
            import_file = state.e_file
            fileformat = os.path.splitext("")
            taskname = state.e_name.text()
            self.lb_PerforceImportPath = QLabel("Perforce Import Path:")
            self.le_PerforceImportPath = QLineEdit()
            self.chb_createInPerforce.layout().addWidget(self.lb_PerforceImportPath)    
            self.chb_createInPerforce.layout().addWidget(self.le_PerforceImportPath)
            self.le_PerforceImportPath.setDisabled(True)
            self.le_PerforceImportPath.setEnabled(False)
            self.preImport(state=state, scenefile=data.get("filename"), importfile=state.e_file.text())
            state.e_file.editingFinished.connect(lambda : self.setP4StateImport(origin, state, stateData))
            state.e_name.editingFinished.connect(lambda : self.setP4StateImport(origin, state, stateData))
            # self.setP4StateImport(origin, state, stateData)
        
        # # Get config from P4V
        try:
            p4path = self.getConfig(category,  self.core.convertPath(entity_path, target="global"))[state_type][taskname][fileformat]
        except Exception as why:
            logger.debug("Get p4path from {} - {} - {}".format(category, state_type, taskname, fileformat))
        else:
            if state_type == "import":
                self.le_PerforceImportPath.setText(p4path)
            else:
                self.le_PerforceExportPath.setText(p4path)
        # if p4path and state_type == "import":
        #     self.p4.connectToPerforce()
        #     state.e_file.setText(self.p4.run_where(p4path)[0].get("fileName", ""))
        if state_layout:
            state_layout.insertWidget(0, self.chb_createInPerforce)

    @err_catcher(name=__name__)
    def onStateDeleted(self, origin, state):
        pass

    @err_catcher(name=__name__)
    def onPublish(self, origin):
        pass

    @err_catcher(name=__name__)
    def postPublish(self, origin, publishType, result):
        """
        origin:         StateManager instance
        publishType:    The type (string) of the publish. 
                        Can be "stateExecution" (state was executed from the context menu) or "publish" (publish button was pressed)
        """

    @err_catcher(name=__name__)
    def onSceneOpen(self, origin, filepath):
        # called when a scenefile gets opened from the Project Browser. Gets NOT called when a scenefile is loaded manually from the file menu in a DCC app.
        pass

    @err_catcher(name=__name__)
    def isPluginActive(self):
        return self.core.getConfig(
            "perforce", "active", configPath=self.core.prismIni
        )

    @err_catcher(name=__name__)
    def onAssetDlgOpen(self, origin, assetDialog):
        pass

    @err_catcher(name=__name__)
    def onAssetCreated(self, origin, assetName, assetPath, assetDialog=None):
        # self.core.getConfig("p4", "assetroot", configPath=os.path.join(assetPath, "perforce.yml"))
        pass

    @err_catcher(name=__name__)
    def onStepDlgOpen(self, origin, dialog):
        """
        Hook up p4 path set in step window
            if p4 path is defined then trigger onCategoryCreated if 'create Default Category' is check
        """
        if not self.isPluginActive():
            return
        self.chb_createInPerforce = QGroupBox("Perforce")
        self.chb_createInPerforce.setCheckable(True)
        self.chb_createInPerforce.setLayout(QVBoxLayout())
        self.chb_createInPerforce.setChecked(True)
        # self.chb_relativeToAssetP4Root = QCheckBox()
        # self.chb_relativeToAssetP4Root.setChecked(True)
        self.lb_PerforcePath = QLabel("Perforce Path:")
        self.le_PerforcePath = QLineEdit()
        self.chb_createInPerforce.layout().addWidget(self.lb_PerforcePath)
        self.chb_createInPerforce.layout().addWidget(self.le_PerforcePath) 
        # self.chb_createInPerforce.layout().addWidget(self.chb_relativeToAssetP4Root) 
        dialog.layout().insertWidget(0, self.chb_createInPerforce)

    @err_catcher(name=__name__)
    def onStepCreated(self, origin, entity, stepname, path, settings):
        # entity: "asset" or "shot"
        # settings: dictionary containing "createDefaultCategory", which holds a boolean (settings["createDefaultCategory"])
        pass

    @err_catcher(name=__name__)
    def onCategoryDlgOpen(self, origin, catDialog):
        p4 = self.core.getConfig(
            "perforce", "active", configPath=self.core.prismIni
        )
        if not p4:
            return
        self.chb_createInPerforce = QGroupBox("Perforce")
        self.chb_createInPerforce.setCheckable(True)
        self.chb_createInPerforce.setLayout(QVBoxLayout())
        self.chb_createInPerforce.setChecked(True)
        # self.chb_relativeToAssetP4Root = QCheckBox()
        # self.chb_relativeToAssetP4Root.setChecked(True)
        self.lb_PerforcePath = QLabel("Perforce Intergrate Path:")
        self.le_PerforcePath = QLineEdit()
        self.chb_createInPerforce.layout().addWidget(self.lb_PerforcePath)    
        self.chb_createInPerforce.layout().addWidget(self.le_PerforcePath) 
        # self.chb_createInPerforce.layout().addWidget(self.chb_relativeToAssetP4Root) 
        catDialog.w_options.layout().insertWidget(0, self.chb_createInPerforce)

    @err_catcher(name=__name__)
    def onCategoryCreated(self, origin, catname, path):
        if hasattr(self, "le_PerforcePath"):
            path, ext = os.path.splitext(path)
            entity_path = os.path.abspath(os.path.join(path, os.pardir, os.pardir, os.pardir))
            entity_path = self.core.convertPath(entity_path, "global")
            try:
                p4path = self.p4.run_where(self.le_PerforcePath.text())[0].get("depotFile", "")
            except:
                return
            else:
                if not ext:
                    self.setConfig({catname: {'root':p4path}}, entity_path)
                else:
                    self.setConfig({os.path.basename(os.path.dirname(path)): {ext:p4path}}, os.path.dirname(entity_path))

    @err_catcher(name=__name__)
    def onShotDlgOpen(self, origin, shotDialog, shotName=None):
        # gets called just before the "Create Shot"/"Edit Shot" dialog opens. Check if "shotName" is None to check if a new shot will be created or if an existing shot will be edited.
        pass
    @err_catcher(name=__name__)
    def onShotCreated(self, origin, sequenceName, shotName):
        pass

    @err_catcher(name=__name__)
    def openPBFileContextMenu(self, origin, rcmenu, filepath):
        if not self.connectToPerforce():
            return
        # gets called before "rcmenu" get displayed. Can be used to modify the context menu when the user right clicks in the scenefile lists of assets or shots in the Project Browser.
        if not os.path.exists(filepath):
            return
        menu_p4 = QMenu("P4")
        a_p4setPath = QAction("Set P4 Path", origin)
        a_p4setPath.triggered.connect(lambda: self.openP4SetPathDialog(origin, filepath))
        a_p4checkin = QAction("Check into P4", origin)
        a_p4checkin.triggered.connect(lambda: self.checkinP4(filepath))
        a_p4import = QAction("Import from P4V", origin)
        a_p4import.triggered.connect(lambda: self.openP4ImportPathDialog(origin, filepath))
        a_p4open = QAction("Open in P4V", origin)
        a_p4open.triggered.connect(lambda: self.openInP4V(filepath))
        menu_p4.addAction(a_p4setPath)
        if os.path.isfile(filepath):
            menu_p4.addAction(a_p4checkin)
            menu_p4.addAction(a_p4import)
        menu_p4.addAction(a_p4open)
        rcmenu.addMenu(menu_p4)

    @err_catcher(name=__name__)
    def openPBListContextMenu(self, origin, rcmenu, listWidget, item, path):
        # gets called before "rcmenu" get displayed for the "Tasks" and "Versions" list in the Project Browser.
        pass

    @err_catcher(name=__name__)
    def openPBAssetContextMenu(self, origin, rcmenu, index):
        """
        origin: Project Browser instance
        rcmenu: QMenu object, which can be modified before it gets displayed
        index: QModelIndex object of the item on which the user clicked. Use index.data() to get the text of the index.
        """
        pass

    @err_catcher(name=__name__)
    def openPBAssetStepContextMenu(self, origin, rcmenu, index):
        pass

    @err_catcher(name=__name__)
    def openPBAssetCategoryContextMenu(self, origin, rcmenu, index):
        pass

    @err_catcher(name=__name__)
    def openPBShotContextMenu(self, origin, rcmenu, index):
        pass

    @err_catcher(name=__name__)
    def openPBShotStepContextMenu(self, origin, rcmenu, index):
        pass

    @err_catcher(name=__name__)
    def openPBShotCategoryContextMenu(self, origin, rcmenu, index):
        pass

    @err_catcher(name=__name__)
    def projectBrowserContextMenuRequested(self, origin, menuType, menu):
        pass

    @err_catcher(name=__name__)
    def openTrayContextMenu(self, origin, rcmenu):
        pass

    @err_catcher(name=__name__)
    def preLoadEmptyScene(self, origin, filepath):
        pass

    @err_catcher(name=__name__)
    def postLoadEmptyScene(self, origin, filepath):
        pass

    @err_catcher(name=__name__)
    def onEmptySceneCreated(self, origin, filepath):
        pass

    @err_catcher(name=__name__)
    def preImport(self, *args, **kwargs):
        print(args, kwargs)
        if not self.isPluginActive():
            return kwargs

        p4path = ""
        data = self.core.entities.getScenefileData(self.core.getCurrentFileName())
        entity_path = self.core.getEntityBasePath(data.get("filename"))
        category = data.get("category")
        state = kwargs['state']
        fileformat = os.path.splitext(kwargs["importfile"])[-1]

        # Get config from P4V
        try:
            p4path = self.getConfig(category,  self.core.convertPath(entity_path, target="global"))["import"][state.e_name.text()][fileformat]
        except Exception as why:
            logger.error("Failed to resolve to p4path.")
            raise
        if hasattr(self, "le_PerforceImportPath"):
            self.le_PerforceImportPath.setText(p4path)
        if p4path:
            self.connectToPerforce()
            try:
                self.p4.run_sync(p4path)
            except P4.P4Exception as why:
                if why.errors:
                    logger.error(why.errors)
                else:
                    logger.info(why.warnings)

            try:
                kwargs["importfile"] = self.p4.run_where(p4path)[0].get("path", kwargs["importfile"])
                state.e_file.setText(kwargs["importfile"])
            except P4.P4Exception as why:
                if why.errors:
                    logger.error("{} import file in not map in p4, {}".format( p4path, why.errors))
        return kwargs

    @err_catcher(name=__name__)
    def postImport(self, *args, **kwargs):
        pass

    @err_catcher(name=__name__)
    def preExport(self, *args, **kwargs):
        pass

    @err_catcher(name=__name__)
    def postExport(self, *args, **kwargs):
        """
            data = {   
                "entity": "asset",
                "entityName": fname[0],
                "fullEntityName": relpath,
                "step": fname[1],
                "category": "",
                "version": fname[2],
                "comment": fname[3],
                "user": fname[4],
                "extension": fname[5],
            }
        """
        if self.isPluginActive() and hasattr(self, "le_PerforceExportPath"):
            if not self.le_PerforceExportPath.text():
                return
        core = self.core
        projectName = core.projectName
        sceneBasePath = core.scenePath
        taskname = kwargs["state"].l_taskName.text()
        scenePath = kwargs["scenefile"]
        startframe = kwargs["startframe"]
        endframe = kwargs["endframe"]
        outputpath = kwargs["outputpath"]

        data = self.core.entities.getScenefileData(scenePath)
        entity_path = self.core.convertPath(self.core.getEntityBasePath(scenePath), target="global")
        category = data.get("category") or ""

        _, fileformat = os.path.splitext(outputpath)
        category = data.get("category")
        try:
            outputtarget = self.getConfig(category, entity_path)['export'][taskname][fileformat]
        except Exception as why:
            self.logger.error(why, entity_path, taskname, fileformat)
            # raise Exception("{}. {}{}{}".format(category, entity_path, taskname, fileformat))
        if outputtarget:
            return self.checkinP4(outputpath, outputtarget)
        # if os.path.isdir(outputpath):
        #     files = glob.glob(outputpath + "/*.fbx")
        #     if files:
        #         outputpath = files[0]
        #     else:
        #         print("Could not found any fbx in {}".format(outputpath))
        #         return

        # fileverinfoPath = core.getVersioninfoPath(scenePath)
        # if not os.path.exists(fileverinfoPath):
        #     print("Missing version info path. Make sure to use Prism to create file")
        #     return
        # config = core.getConfig(configPath = fileverinfoPath)
        # entityName = config.get("entityName")

        # try:
        #     from P4 import P4
        # except:
        #     print("Missing P4 Module to continue import step")
        #     return
            
        # p4 = P4()
        # p4.connect()
        # output_target_path = checkinP4(p4, core, projectName, entityName, config, sceneBasePath, shotBasePath, task_name, scenePath, startframe, endframe, outputpath)
        # if not output_target_path:
        #     editorpath = p4.run_where("//UnrealBase/cosmic_shake_engine/Engine")[0]['path']
        #     projectpath = p4.run_where("//CosmicShake/mainline/Game/CosmicShake")[0]['path']
        #     output_target_path = os.path.join(os.path.dirname(outputpath), task_name+".fbx")
        #     shutil.copyfile(outputpath, output_target_path)
        #     if os.path.exists(output_target_path):
        #         try:
        #             export_to_unreal(core, editorpath, projectpath, shotBasePath, scenePath, entityName, task_name, output_target_path)
        #         finally:
        #             os.remove(output_target_path)

    @err_catcher(name=__name__)
    def prePlayblast(self, *args, **kwargs):
        pass

    @err_catcher(name=__name__)
    def postPlayblast(self, *args, **kwargs):
        pass

    @err_catcher(name=__name__)
    def preRender(self, *args, **kwargs):
        pass

    @err_catcher(name=__name__)
    def postRender(self, *args, **kwargs):
        pass

    @err_catcher(name=__name__)
    def maya_export_abc(self, origin, params):
        """
        origin: reference to the Maya Plugin class
        params: dict containing the mel command (params["export_cmd"])

        Gets called immediately before Prism exports an alembic file from Maya
        This function can modify the mel command, which Prism will execute to export the file.

        Example:
        print params["export_cmd"]
        >>AbcExport -j "-frameRange 1000 1000 -root |pCube1  -worldSpace -uvWrite -writeVisibility  -file \"D:\\\\Projects\\\\Project\\\\03_Workflow\\\\Shots\\\\maya-001\\\\Export\\\\Box\\\\v0001_comment_rfr\\\\centimeter\\\\shot_maya-001_Box_v0001.abc\"" 

        Use python string formatting to modify the command:
        params["export_cmd"] = params["export_cmd"][:-1] + " -attr material" + params["export_cmd"][-1]
        """

    @err_catcher(name=__name__)
    def preSubmit_Deadline(self, origin, jobInfos, pluginInfos, arguments):
        """
        origin: reference to the Deadline plugin class
        jobInfos: List containing the data that will be written to the JobInfo file. Can be modified.
        pluginInfos: List containing the data that will be written to the PluginInfo file. Can be modified.
        arguments: List of arguments that will be send to the Deadline submitter. This contains filepaths to all submitted files (note that they are eventually not created at this point).

        Gets called before a render or simulation job gets submitted to the Deadline renderfarmmanager.
        This function can modify the submission parameters.

        Example:
        jobInfos["PostJobScript"] = "D:/Scripts/Deadline/myPostJobTasks.py"

        You can find more available job parameters here:
        https://docs.thinkboxsoftware.com/products/deadline/10.0/1_User%20Manual/manual/manual-submission.html
        """

    @err_catcher(name=__name__)
    def postSubmit_Deadline(self, origin, result):
        """
        origin: reference to the Deadline plugin class
        result: the return value from the Deadline submission.
        """

    @err_catcher(name=__name__)
    def preIntegrationAdded(self, origin, integrationFiles):
        """
        origin: reference to the integration class instance
        integrationFiles: dict of files, which will be used for the integration

        Modify the integrationFiles paths to replace the default Prism integration files with custom ones
        """

    #P4 Function

    @err_catcher(name=__name__)
    def setP4StateImport(self, origin, state, stateData, p4path = ""):
        if not p4path:
            p4path = state.e_file.text()
        if not p4path:
            return
        p4path = self.preImport(state=state, scenefile=self.core.getCurrentFileName(), importfile=p4path)['importfile']
        # self.connectToPerforce()
        try:
            resolve_p4path = self.p4.run_where(p4path)
        except P4.P4Exception as why:
            QMessageBox.critical(self.core.messageParent, "Perforce Error", "{} is not valid P4 path. {}".format(p4path, why))
            raise

        resolve_p4path = resolve_p4path[0].get("depotFile", "")
        if not resolve_p4path:
            logger.warn("{} is not a p4 file".format(p4path))
            return
        taskname = "P4_{}".format(os.path.splitext(os.path.basename(p4path))[0])
        
        data = self.core.entities.getScenefileData(self.core.getCurrentFileName())
        entity_path = self.core.getEntityBasePath(data.get("filename"))
        fileformat = os.path.splitext(p4path)[-1]
        resolve_p4path = "".join([os.path.splitext(resolve_p4path)[0], fileformat])
        self.le_PerforceImportPath.setText(resolve_p4path)
            # self.e_name.setText(taskname)
        category = data.get("category")
        
        entity_path = self.core.convertPath(entity_path, target="global")
        self.setConfig({category: {"import":{taskname:{fileformat: resolve_p4path}}}}, entity_path)

    @err_catcher(name=__name__)
    def setP4StateExport(self, origin, state, stateData, p4path = ""):
        if not p4path:
            p4path = self.le_PerforceExportPath.text()
        if not p4path:
            return

        try:
            resolve_p4path = self.p4.run_where(p4path)
        except P4.P4Exception as why:
            QMessageBox.critical(self.core.messageParent, "Perforce Error", "{} is not valid P4 path. {}".format(p4path, why))
            raise

        resolve_p4path = resolve_p4path[0].get("depotFile", "")
        if not resolve_p4path:
            logger.warn("{} is not a p4 file".format(p4path))
            return
        taskname = state.l_taskName.text()
        
        self.le_PerforceExportPath.setText(resolve_p4path)
        data = self.core.entities.getScenefileData(self.core.getCurrentFileName())
        entity_path = self.core.getEntityBasePath(data.get("filename"))
        fileformat = state.cb_outType.currentText()
        # if not resolve_p4path.endswith(fileformat):
        resolve_p4path = "".join([os.path.splitext(resolve_p4path)[0], fileformat])
        category = data.get("category")
        
        entity_path = self.core.convertPath(entity_path, target="global")
        self.setConfig({category: {"export":{taskname:{fileformat: resolve_p4path}}}}, entity_path)

    @err_catcher(name=__name__)
    def connectToPerforce(self, retry=3, show_message=False):
        # if (
        #     not hasattr(self, "p4")
        #     or not hasattr(self, "sgPrjId")
        #     or (user and not hasattr(self, "sgUserId"))
        # ):
        is_connected_p4 = False
        try:
            self.p4.disconnect()
        except:
            pass
        try:
            self.p4.port = self.core.getConfig("perforce", "port", configPath = self.core.prismIni)
            self.p4.user = self.core.getConfig("perforce", "p4username")
            self.p4.client = self.core.getConfig("perforce", "p4userworkspacename")
            self.p4.password = self.core.getConfig("perforce", "p4userpassword")
        except AttributeError as why:
            logger.error(why)
            return
        try:
            self.p4.connect()
        except P4.P4Exception as why:
            raise P4.P4Exception("Failed to connect to p4. {}".format(why))
        try:
            self.p4.run_login('-s')
            is_connected_p4 = True
        except P4.P4Exception as why:
            try:
                self.p4.run_login()
                is_connected_p4 = True
            except P4.P4Exception as why:
                if show_message and retry == 0:
                    QMessageBox.critical(self.core.messageParent, "Perforce Error", "Failed to login to p4. {}".format(why))
        while not is_connected_p4 and retry != 0:
            time.sleep(1)
            is_connected_p4 = self.connectToPerforce(retry-1)
        if show_message and is_connected_p4:
            QMessageBox.information(self.core.messageParent, "Perforce", "Successfully connect to {} with user {}".format(self.p4.port, self.p4.user))
        
        if hasattr(self, "connectStatusWidget"):
            self.connectStatusWidget = is_connected_p4

        return is_connected_p4

    @err_catcher(name=__name__)
    def getConfigPath(self, rootPath):
        return os.path.join(rootPath,"perforce.yml")

    @err_catcher(name=__name__)
    def getConfig(self, param, configRoot):
        return self.core.getConfig("perforce", param, configPath=self.getConfigPath(configRoot))

    @err_catcher(name=__name__)
    def setConfig(self, data, configRoot):
        data = {'perforce':data}
        self.core.setConfig(data=data, configPath=self.getConfigPath(configRoot))
        self.core.configs.clearCache()


    @err_catcher(name=__name__)
    def openP4SetPathDialog(self, origin, filepath):
        # get current tab and selected file
        if not self.isPluginActive():
            return
        rawpath, ext = os.path.splitext(filepath)
        entity_path = self.core.getEntityBasePath(filepath)
        entity_path = self.core.convertPath(entity_path, "global")
        cat = os.path.basename(os.path.dirname(filepath)) if ext else os.path.basename(filepath)
        data = self.getConfig(cat, entity_path) or ""
        if data:
            data = data.get("path") or data.get(ext) or ""
        dlg_settings = QDialog()
        dlg_settings.setWindowTitle("Set P4 Path")
        dlg_settings.bb_settings = QDialogButtonBox()
        def accept_dlg():
            self.onCategoryCreated(origin, os.path.basename(filepath), filepath)
            dlg_settings.accept()
        def reject_dlg():
            dlg_settings.reject()
        dlg_settings.bb_settings.addButton("Accept", QDialogButtonBox.AcceptRole)
        dlg_settings.bb_settings.addButton("Cancel", QDialogButtonBox.RejectRole)
        dlg_settings.bb_settings.accepted.connect(accept_dlg)
        dlg_settings.bb_settings.rejected.connect(reject_dlg)


        self.chb_createInPerforce = QGroupBox("Perforce")
        # self.chb_createInPerforce.setCheckable(True)
        self.chb_createInPerforce.setLayout(QVBoxLayout())
        self.chb_createInPerforce.setChecked(True)
        self.lb_filePath = QLabel(filepath)
        self.lb_PerforcePath = QLabel("Perforce root path:")
        self.le_PerforcePath = QLineEdit(text=data)
        self.chb_createInPerforce.layout().addWidget(self.lb_filePath)
        self.chb_createInPerforce.layout().addWidget(self.lb_PerforcePath)    
        self.chb_createInPerforce.layout().addWidget(self.le_PerforcePath) 

        lo_settings = QVBoxLayout()
        lo_settings.addWidget(self.chb_createInPerforce)
        lo_settings.addWidget(dlg_settings.bb_settings)
        dlg_settings.setLayout(lo_settings)
        dlg_settings.setParent(self.core.messageParent, Qt.Window)
        action = dlg_settings.exec_()

        if action == 0:
            return

    @err_catcher(name=__name__)
    def openP4ImportPathDialog(self, origin, filepath):
        # get current tab and selected file
        if not self.isPluginActive():
            return
        rawpath, ext = os.path.splitext(filepath)
        entity_path = self.core.getEntityBasePath(filepath)
        entity_path = self.core.convertPath(entity_path, "global")
        cat = os.path.basename(os.path.dirname(filepath)) if ext else os.path.basename(filepath)
        data = self.getConfig(cat, entity_path) or ""
        if data:
            data = data.get("path") or data.get(ext) or ""
        dlg_settings = QDialog()
        dlg_settings.setWindowTitle("Import File From P4")
        dlg_settings.bb_settings = QDialogButtonBox()
        def accept_dlg():
            self.importFromP4(origin, filepath, self.le_PerforcePath.text())
            dlg_settings.accept()
        def reject_dlg():
            dlg_settings.reject()
        dlg_settings.bb_settings.addButton("Accept", QDialogButtonBox.AcceptRole)
        dlg_settings.bb_settings.addButton("Cancel", QDialogButtonBox.RejectRole)
        dlg_settings.bb_settings.accepted.connect(accept_dlg)
        dlg_settings.bb_settings.rejected.connect(reject_dlg)

        self.chb_createInPerforce = QGroupBox("Perforce")
        # self.chb_createInPerforce.setCheckable(True)
        self.chb_createInPerforce.setLayout(QVBoxLayout())
        self.chb_createInPerforce.setChecked(True)
        self.lb_filePath = QLabel(filepath)
        self.lb_PerforcePath = QLabel("Perforce import path:")
        self.le_PerforcePath = QLineEdit(text=data)
        self.chb_createInPerforce.layout().addWidget(self.lb_filePath)
        self.chb_createInPerforce.layout().addWidget(self.lb_PerforcePath)    
        self.chb_createInPerforce.layout().addWidget(self.le_PerforcePath) 

        lo_settings = QVBoxLayout()
        lo_settings.addWidget(self.chb_createInPerforce)
        lo_settings.addWidget(dlg_settings.bb_settings)
        dlg_settings.setLayout(lo_settings)
        dlg_settings.setParent(self.core.messageParent, Qt.Window)
        action = dlg_settings.exec_()

        if action == 0:
            return

    @err_catcher(name=__name__)
    def os_removefile(self, filepath):
        try:
            os.remove(filepath)
        except:
            p = subprocess.Popen(["powershell","-WindowStyle", "Hidden", "-ExecutionPolicy", "ByPass", "-Command", "Remove-Item", "-Force", filepath], shell=True)
            p.communicate()

    @err_catcher(name=__name__)
    def importFromP4(self, origin, filepath, p4path):
        fnameData = self.core.getScenefileData(filepath)
        cat = os.path.dirname(filepath)
        if not self.connectToPerforce(show_message=False):
            return
        workspacep4path = self.p4.run_where(p4path)[0].get('path')
        if not os.path.exists(workspacep4path):
            try:
                self.p4.run_sync(p4path)
            except P4.P4Exception as why:
                QMessageBox.critical(self.core.messageParent, "Perforce Error", "{} is not exists or cannot be sync.{}".format(p4path, why))
                raise
        try:
            dstfilepath = self.core.generateScenePath(
                entity=fnameData["entity"],
                entityName=fnameData["entityName"],
                step=fnameData["step"],
                category=fnameData["category"],
                comment="Import-From-P4V",
                basePath=self.core.paths.getEntityBasePath(filepath),
                extension=fnameData["extension"],
            )
            shutil.copyfile(workspacep4path, dstfilepath)
        except:
            QMessageBox.critical(self.core.messageParent, "Perforce", "Failed to import p4 file {}".format(p4path))
            raise
        self.onCategoryCreated(origin, cat, filepath)
        # self.core.addToRecent(workspacep4path)
        


        #Mannualy refresh Project Browser
        if hasattr(self.core, "pb"):
        #     self.core.pb.setRecent()
            self.core.pb.refreshUI()
        QMessageBox.information(self.core.messageParent, "Perforce", "Successfully import p4 file {}".format(p4path))

    @err_catcher(name=__name__)
    def openInP4V(self, filepath = ""):
        rawpath, ext = os.path.splitext(filepath)
        self.core.convertPath(filepath, "global")
        data = self.core.entities.getScenefileData(filepath)
        category = data.get("category")
        p4path = self.getConfig(category, self.core.convertPath(self.core.getEntityBasePath(filepath), "global"))
        cmd = ["p4v", "-p", self.p4.port, "-u", self.p4.user, "-c", self.p4.client ]
        if p4path:
            p4path = p4path.get(ext)
            if p4path:
                cmd.extend(["-s", p4path])
        subprocess.Popen(cmd)

    @err_catcher(name=__name__)
    def checkinP4(self, filepath, p4path=""):
        if not self.connectToPerforce(show_message=False):
            return
        if not p4path:
            rawpath, ext = os.path.splitext(filepath)
            self.core.convertPath(filepath, "global")
            data = self.core.entities.getScenefileData(filepath)
            category = data.get("category")
            p4path = self.getConfig(category, self.core.convertPath(self.core.getEntityBasePath(filepath), "global"))
            if p4path:
                p4path = p4path.get(ext)
        if not p4path:
            return
        try:
            p4path = self.p4.run_where(p4path)[0].get("path")
        except P4.P4Exception as why:    
            self.logger.error("Failed to resolve {} to p4 path.\n {}".format(p4path, why))
            return
        
        try:
            os.makedirs(os.path.dirname(p4path))
        except:
            pass

        try:
            if os.path.exists(p4path):
                self.os_removefile(p4path)
        except Exception as why:
            logger.error("Encountered issue remove {}.\n{}".format(p4path, why))
        else:
            try:
                shutil.copy(filepath, p4path)
                self.p4.run_reconcile(p4path)
            except P4.P4Exception as why:
                logger.error("Failed to check in {} to self.P4. \n {}".format(p4path, why))
            else:
                logger.info("Interate {} to P4 success. Please check your pending changelist.".format(p4path))
        QMessageBox.information(self.core.messageParent, "Perforce", "Successfully check in {} .Please check your pending changelist.".format(p4path))
        subprocess.Popen(["p4v", "-p", self.p4.port, "-u", self.p4.user, "-c", self.p4.client ])
        return p4path
