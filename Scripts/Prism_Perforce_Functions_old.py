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


import os
import sys

import subprocess

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

if sys.version[0] == "3":
    pVersion = 3
else:
    pVersion = 2

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

import os

try:
    import P4
except:
    modulePath = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "external_modules/p4_api{}".format(pVersion))
    if not modulePath in sys.path:
        sys.path.append(modulePath)
    import P4

import P4Publish
class P4Connection:
    connected = "Connected"
    disconnected = "Disconnected"


class Prism_Perforce_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.p4 = P4.P4()

        self.callbacks = []
        self.registerCallbacks()

    @err_catcher(name=__name__)
    def isActive(self):
        return True

    @err_catcher(name=__name__)
    def registerCallbacks(self):
        pass
        # self.callbacks.append(self.core.registerCallback("projectBrowser_getAssetMenu", self.projectBrowser_getAssetMenu))
        # self.callbacks.append(self.core.registerCallback("projectBrowser_getShotMenu", self.projectBrowser_getShotMenu))


    @err_catcher(name=__name__)
    def onProjectChanged(self, origin):
        pass

    @err_catcher(name=__name__)
    def connectP4(self, origin):
        pass

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
            lambda x: self.connectToPerforce()
        )

    @err_catcher(name=__name__)
    def prismSettings_p4Toggled(self, origin, checked):
        origin.w_Perforce.setVisible(checked)

    @err_catcher(name=__name__)
    def pbBrowser_getMenu(self, origin):
        p4 = self.core.getConfig(
            "perforce", "active", configPath=self.core.prismIni
        )
        if p4:
            p4Menu = QMenu("perforce", origin)

            actp4 = QAction("Open Perforce", origin)
            actp4.triggered.connect(self.openp4)
            p4Menu.addAction(actp4)

            p4Menu.addSeparator()

            actSSL = QAction("Perforce assets to local", origin)
            actSSL.triggered.connect(lambda: self.p4AssetsToLocal(origin))
            p4Menu.addAction(actSSL)

            actSSL = QAction("Local assets to Perforce", origin)
            actSSL.triggered.connect(lambda: self.p4AssetsTop4(origin))
            p4Menu.addAction(actSSL)

            p4Menu.addSeparator()

            actSSL = QAction("Perforce shots to local", origin)
            actSSL.triggered.connect(lambda: self.p4ShotsToLocal(origin))
            p4Menu.addAction(actSSL)

            actLSS = QAction("Local shots to Perforce", origin)
            actLSS.triggered.connect(lambda: self.p4ShotsTop4(origin))
            p4Menu.addAction(actLSS)

            return p4Menu

    @err_catcher(name=__name__)
    def prismSettings_loadSettings(self, origin, settings):
        if "perforce" in settings:
            if "p4username" in settings["perforce"]:
                origin.e_p4UserName.setText(settings["perforce"]["p4username"])

            if "p4userpassword" in settings["perforce"]:
                origin.e_p4UserPassword.setText(settings["perforce"]["p4userpassword"])

            if "p4userworkspacename" in settings["perforce"]:
                origin.e_p4userworkspacename.setText(settings["perforce"]["p4userworkspacename"])

            if "p4userworkspaceroot" in settings["perforce"]:
                origin.e_p4userworkspaceroot.setText(settings["perforce"]["p4userworkspaceroot"])

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

            if "defaultusername" in settings["perforce"]:
                if not origin.e_p4UserName.text():
                    origin.e_p4UserName.setText(settings["perforce"]["defaultusername"])

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

    @err_catcher(name=__name__)
    def createAsset_open(self, origin):
        p4 = self.core.getConfig(
            "perforce", "active", configPath=self.core.prismIni
        )
        if not p4:
            return

        origin.chb_createInPerforce = QCheckBox("Create asset in Perforce")
        origin.e_PerforcePath = QLineEdit("Create asset in Perforce")
        origin.w_options.layout().insertWidget(0, origin.chb_createInPerforce)
        origin.chb_createInPerforce.setChecked(True)

    @err_catcher(name=__name__)
    def createAsset_typeChanged(self, origin, state):
        if hasattr(origin, "chb_createInPerforce"):
            origin.chb_createInPerforce.setEnabled(state)

    @err_catcher(name=__name__)
    def assetCreated(self, origin, itemDlg, assetPath):
        if (
            hasattr(itemDlg, "chb_createInPerforce")
            and itemDlg.chb_createInPerforce.isChecked()
        ):
            self.createp4Assets([assetPath])

    @err_catcher(name=__name__)
    def editShot_open(self, origin, shotName):
        if shotName is None:
            p4 = self.core.getConfig(
                "perforce", "active", configPath=self.core.prismIni
            )
            if not p4:
                return

            origin.chb_createInPerforce = QCheckBox("Create shot in Perforce")
            origin.widget.layout().insertWidget(0, origin.chb_createInPerforce)
            origin.chb_createInPerforce.setChecked(True)

    @err_catcher(name=__name__)
    def editShot_closed(self, origin, shotName):
        if (
            hasattr(origin, "chb_createInPerforce")
            and origin.chb_createInPerforce.isChecked()
        ):
            self.createp4Shots([shotName])

    @err_catcher(name=__name__)
    def pbBrowser_getPublishMenu(self, origin):
        p4 = self.core.getConfig(
            "perforce", "active", configPath=self.core.prismIni
        )
        if (
            p4
            and origin.seq
        ):
            p4Act = QAction("Publish to Perforce", origin)
            p4Act.triggered.connect(lambda: self.p4Publish(origin))
            return p4Act

    @err_catcher(name=__name__)
    def connectToPerforce(self, user=True):
        # if (
        #     not hasattr(self, "p4")
        #     or not hasattr(self, "sgPrjId")
        #     or (user and not hasattr(self, "sgUserId"))
        # ):
        self.p4.port = self.core.getConfig("perforce", "port", configPath = self.core.prismIni)
        self.p4.user = self.core.getConfig("perforce", "p4username")
        self.p4.client = self.core.getConfig("perforce", "p4userworkspacename")
        self.p4.password = self.core.getConfig("perforce", "p4userpassword")
        if self.p4.connected():
            self.p4.disconnect()
        self.p4.connect()
        try:
            self.p4.run_login('-s')
        except P4.P4Exception as why:
            try:
                self.p4.run_login()
            except P4.P4Exception as why:
                QMessageBox.error(self.core.messageParent, "Perforce Error", "Failed to login to p4. {}".format(why))
        QMessageBox.information(self.core.messageParent, "Perforce", "Successfully connect to {} with user {}".format(self.p4.port, self.p4.user))

    @err_catcher(name=__name__)
    def createp4Assets(self, assets=[]):
        for asset in assets:
            data = {
                "p4path": ""
            }
            self.core.setConfig(
                data=data, 
                configPath=os.path.join(asset, "p4info.yml")
                )

    @err_catcher(name=__name__)
    def createp4Shots(self, shots=[]):
        pass

    @err_catcher(name=__name__)
    def p4Publish(self, origin):
        if origin.tbw_browser.currentWidget().property("tabType") == "Assets":
            pType = "Asset"
        else:
            pType = "Shot"

        shotName = os.path.basename(origin.renderBasePath)

        taskName = (
            origin.curRTask.replace(" (playblast)", "")
            .replace(" (2d)", "")
            .replace(" (external)", "")
        )
        versionName = origin.curRVersion.replace(" (local)", "")
        mpb = origin.mediaPlaybacks["shots"]

        imgPaths = []
        if mpb["prvIsSequence"] or len(mpb["seq"]) == 1:
            if os.path.splitext(mpb["seq"][0])[1] in [".mp4", ".mov"]:
                imgPaths.append(
                    [os.path.join(mpb["basePath"], mpb["seq"][0]), mpb["curImg"]]
                )
            else:
                imgPaths.append(
                    [os.path.join(mpb["basePath"], mpb["seq"][mpb["curImg"]]), 0]
                )
        else:
            for i in mpb["seq"]:
                imgPaths.append([os.path.join(mpb["basePath"], i), 0])

        if "pstart" in mpb:
            sf = mpb["pstart"]
        else:
            sf = 0

        # do publish here

    def openp4(self, shotName=None, eType="Shot", assetPath=""):
        import subprocess
        p4port = self.core.getConfig("perforce", "port", configPath=self.core.prismIni)
        p4user = self.core.getConfig("perforce", "p4username")
        p4client = self.core.getConfig("perforce", "p4userworkspacename")
        
        
        subprocess.run(['p4v', '-p', p4port, '-u', p4user, '-c', p4client])


    @err_catcher(name=__name__)
    def p4AssetsToLocal(self, origin):
        # add code here

        createdAssets = []
        if len(createdAssets) > 0:
            msgString = "The following assets were created:\n\n"

            createdAssets.sort()

            for i in createdAssets:
                msgString += i + "\n"
        else:
            msgString = "No assets were created."

        QMessageBox.information(self.core.messageParent, "Perforce Sync", msgString)

        origin.refreshAHierarchy()

    @err_catcher(name=__name__)
    def p4AssetsTop4(self, origin):
        # add code here

        msgString = "No assets were created or updated."

        QMessageBox.information(self.core.messageParent, "Perforce Sync", msgString)

    @err_catcher(name=__name__)
    def p4ShotsToLocal(self, origin):
        # add code here

        origin.refreshShots()

    @err_catcher(name=__name__)
    def p4ShotsTop4(self, origin):
        # add code here

        msgString = "No shots were created or updated."

        QMessageBox.information(self.core.messageParent, "Perforce Sync", msgString)

    @err_catcher(name=__name__)
    def onProjectBrowserClose(self, origin):
        pass

    @err_catcher(name=__name__)
    def onSetProjectStartup(self, origin):
        pass
