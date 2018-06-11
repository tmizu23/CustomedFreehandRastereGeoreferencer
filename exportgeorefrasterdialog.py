# -*- coding: utf-8 -*-
"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os.path

from PyQt4.QtGui import QDialog, QFileDialog, QMessageBox
from ui_exportgeorefrasterdialog import Ui_ExportGeorefRasterDialog


class ExportGeorefRasterDialog(QDialog,
                               Ui_ExportGeorefRasterDialog):

    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)

        self.pushButtonBrowse.clicked.connect(self.showBrowserDialog)

    def clear(self, layer):
        self.lineEditImagePath.setText("")
        self.checkBoxRotationMode.setChecked(False)

        defaultPath, _ = os.path.splitext(layer.filepath)
        self.defaultPath = defaultPath + "_georeferenced.png"

    def showBrowserDialog(self):
        if self.lineEditImagePath.text():
            filepathDialog = self.lineEditImagePath.text()
        else:
            filepathDialog = self.defaultPath

        filepath = QFileDialog.getSaveFileName(
            None, "Export georeferenced raster", filepathDialog,
            "Images (*.png *.bmp *.jpg *.tif)")

        if filepath:
            self.lineEditImagePath.setText(filepath)

    def accept(self):
        result, message, details = self.validate()
        if result:
            self.done(QDialog.Accepted)
        else:
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Error")
            msgBox.setText(message)
            msgBox.setDetailedText(details)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()

    def validate(self):
        result = True
        message = ""
        details = ""

        self.isPutRotationInWorldFile = self.checkBoxRotationMode.isChecked()

        self.imagePath = self.lineEditImagePath.text()
        if not self.imagePath:
            result = False
            details += "A file must be selected"

        if result:
            _, extension = os.path.splitext(self.imagePath)
            extension = extension.lower()
            if extension not in [".jpg", ".bmp", ".png", ".tif"]:
                result = False
                if len(details) > 0:
                    details += "\n"
                details += "The file must be an image"

        if not result:
            message = "There were errors in the form"

        return result, message, details
