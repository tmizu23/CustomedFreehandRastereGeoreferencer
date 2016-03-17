# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TileLayer Plugin
                                 A QGIS plugin
 Plugin layer for Tile Maps
                             -------------------
        begin                : 2012-12-16
        copyright            : (C) 2013 by Minoru Akagi
        email                : akaginch@gmail.com
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_propertiesdialog import Ui_Dialog

class PropertiesDialog(QDialog, Ui_Dialog):
    def __init__(self, layer):
        QDialog.__init__(self)
        # set up the user interface
        self.setupUi(self)
        self.setWindowTitle(u"%s - %s" % (self.tr("Layer Properties"), layer.name()))
        
        self.layer = layer
        self.horizontalSlider_Transparency.valueChanged.connect(self.sliderChanged)
        self.spinBox_Transparency.valueChanged.connect(self.spinBoxChanged)
        
        self.textEdit_Properties.setText(layer.metadata())
        self.spinBox_Transparency.setValue(layer.transparency)
    
    def sliderChanged(self, val):
        s = self.spinBox_Transparency
        s.blockSignals(True)
        s.setValue(val)
        s.blockSignals(False)
    
    def spinBoxChanged(self, val):
        s = self.horizontalSlider_Transparency
        s.blockSignals(True)
        s.setValue(val)
        s.blockSignals(False)
