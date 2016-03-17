# -*- coding: utf-8 -*-
 
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import os
import math

class RasterShadowMapCanvasItem(QgsMapCanvasItem):
    
    def __init__(self, canvas):
        QgsMapCanvasItem.__init__(self, canvas)
        
        self.canvas = canvas
        self.reset()
        
    def reset(self, layer=None):
        self.layer = layer
        self.setVisible(False)
        
        self.dx = 0
        self.dy = 0
        self.drotation = 0
        self.fxscale = 1
        self.fyscale = 1
        
    def setDeltaDisplacement(self, dx, dy, doUpdate):
        self.dx = dx
        self.dy = dy
        if doUpdate:
            self.setVisible(self.layer <> None)
            self.updateRect()
            self.update()
    
    def setDeltaRotation(self, rotation, doUpdate):
        self.drotation = rotation
        if doUpdate:
            self.updateRect()
            self.update()
        
    def setDeltaScale(self, xscale, yscale, doUpdate):
        self.fxscale = xscale
        self.fyscale = yscale
        if doUpdate:
            self.updateRect()
            self.update()
        
    def updateRect(self):
        topLeft, topRight, bottomRight, bottomLeft = self.cornerCoordinates()
       
        left = min(topLeft.x(), topRight.x(), bottomRight.x(), bottomLeft.x())
        right = max(topLeft.x(), topRight.x(), bottomRight.x(), bottomLeft.x())
        top = max(topLeft.y(), topRight.y(), bottomRight.y(), bottomLeft.y())
        bottom = min(topLeft.y(), topRight.y(), bottomRight.y(), bottomLeft.y())
        
        self.setRect(QgsRectangle(left, bottom, right, top))
    
    def cornerCoordinates(self):
        center = QgsPoint(self.layer.center.x() + self.dx, self.layer.center.y() + self.dy)
        return self.layer.transformedCornerCoordinates(center, 
                                                 self.layer.rotation, self.layer.xScale, self.layer.yScale)
        
    def paint(self, painter, options, widget): 
        painter.save()
        self.prepareStyle(painter)
        self.drawRaster(painter)
        painter.restore()
     
    def drawRaster(self, painter):
        mapUPerPixel = self.canvas.mapUnitsPerPixel()
        
        scaleX = self.layer.xScale * self.fxscale / mapUPerPixel
        scaleY = self.layer.yScale * self.fyscale / mapUPerPixel
        
        rect = QRect(QPoint(round(-self.layer.image.width() / 2.0), 
                            round(-self.layer.image.height() / 2.0 )), 
                     QPoint(round(self.layer.image.width() / 2.0 ), 
                            round(self.layer.image.height() / 2.0 )))
        targetRect = self.boundingRect() 
        
        # draw the image on the canvas item rectangle
        # center displacement already taken into account in canvas item rectangle
        # so no update
        painter.translate(targetRect.center())
        painter.rotate(self.layer.rotation + self.drotation)
        painter.scale(scaleX, scaleY)
        painter.drawImage(rect, self.layer.image)

    def prepareStyle(self, painter):
        painter.setOpacity(min(0.5, 1 - self.layer.transparency / 100.0))
