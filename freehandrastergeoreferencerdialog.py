# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FreehandRasterGeoreferencerDialog
                                 A QGIS plugin
 Interactive georeferencing of rasters
                             -------------------
        begin                : 2014-05-21
        copyright            : (C) 2014 by GV
        email                : guilhem.vellut@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import QgsProject
from ui_freehandrastergeoreferencer import Ui_FreehandRasterGeoreferencer
import utils
import os.path
import string


class FreehandRasterGeoreferencerDialog(QtGui.QDialog, Ui_FreehandRasterGeoreferencer):
    
    
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        
        QObject.connect(self.pushButtonBrowse,SIGNAL("clicked()"),self.showBrowserDialog)
        QObject.connect(self.checkBoxUseScale,SIGNAL("clicked()"),self.setUseScale)

    def clear(self):
        self.lineEditImagePath.setText("")
        self.checkBoxUseScale.setChecked(False)
    
    def setUseScale(self):
        state = self.checkBoxUseScale.isChecked()
        self.doubleSpinBoxScale.setEnabled(state)
        self.doubleSpinBoxDPI.setEnabled(state)

    def showBrowserDialog(self):
        bDir,found = QgsProject.instance().readEntry(utils.SETTINGS_KEY, 
                    utils.SETTING_BROWSER_RASTER_DIR, None)
        if not found:
            bDir = os.path.expanduser("~")
            
        qDebug(repr(bDir))
        filepath = u'%s'%(QFileDialog.getOpenFileName(self, "Select image", bDir, "Images (*.png *.bmp *.jpg *.tif *.pdf)"))
        self.lineEditImagePath.setText(filepath)
        
        if filepath:
            bDir,_=os.path.split(filepath)
            QgsProject.instance().writeEntry(utils.SETTINGS_KEY, 
                    utils.SETTING_BROWSER_RASTER_DIR, bDir)
            

    def accept(self):
        result, message, details = self.validate()
        if result:
            self.done(QtGui.QDialog.Accepted)
        else:
            msgBox = QtGui.QMessageBox()
            msgBox.setWindowTitle(u"Error")
            msgBox.setText(message)
            msgBox.setDetailedText(details)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()

    def validate(self):
        result = True
        message = ""
        details = ""
        
        self.imagePath = self.lineEditImagePath.text()
        _, extension = os.path.splitext(self.imagePath)
        extension = string.lower(extension)
        if not os.path.isfile(self.imagePath) or (extension != ".jpg" and extension != ".bmp" and extension != ".png" and extension != ".tif" and extension != ".pdf"):
            result = False
            if len(details) > 0:
                details += '\n'
            details += u"The path must be an image file"

        if not result:
            message = "There were errors in the form"

        return result, message, details
        
