# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import QgsMessageBar
from loaderrordialog import LoadErrorDialog
import os
import math
import utils

class LayerDefaultSettings:
    TRANSPARENCY = 30
    BLEND_MODE = "SourceOver"

class FreehandRasterGeoreferencerLayer(QgsPluginLayer):

    LAYER_TYPE = "FreehandRasterGeoreferencerLayer"

    def __init__(self, plugin, filepath, title, screenExtent,useScale, scale, dpi):
        QgsPluginLayer.__init__(self, FreehandRasterGeoreferencerLayer.LAYER_TYPE, title)
        self.plugin = plugin
        self.iface = plugin.iface

        self.title = title
        self.filepath = filepath

        # set custom properties
        self.setCustomProperty("title", title)
        self.setCustomProperty("filepath", self.filepath)

        self.setValid(True)

        self.setTransparency(LayerDefaultSettings.TRANSPARENCY)
        self.setBlendModeByName(LayerDefaultSettings.BLEND_MODE)

        # dummy data: real init is done in intializeLayer
        self.center = QgsPoint(0, 0)
        self.rotation = 0.0
        self.xScale = 1.0
        self.yScale = 1.0

        self.useScale = useScale
        self.scale = scale
        self.dpi = dpi

        self.error = False
        self.initializing = False
        self.initialized = False
        self.initializeLayer(screenExtent)
        self._extent = None

    def replaceRaster(self, filepath, title):
        self.title = title
        self.filepath = filepath

        # set custom properties
        self.setCustomProperty("title", title)
        self.setCustomProperty("filepath", self.filepath)
        reader = QImageReader(filepath)
        self.image = reader.read()
        self.repaint()

    def setScale(self, xScale, yScale):
        self.xScale = xScale
        self.yScale = yScale

    def setRotation(self, rotation):
        if rotation > 360:
            rotation -= 360
        elif rotation < 0:
            rotation += 360
        self.rotation = rotation

    def setCenter(self, center):
        self.center = center

    def commitTransformParameters(self):
        QgsProject.instance().dirty(True)
        self._extent = None
        self.setCustomProperty("xScale", self.xScale)
        self.setCustomProperty("yScale", self.yScale)
        self.setCustomProperty("rotation", self.rotation)
        self.setCustomProperty("xCenter", self.center.x())
        self.setCustomProperty("yCenter", self.center.y())

    def resetTransformParametersToNewCrs(self):
        """
        Attempts to keep the layer on the same region of the mpa when
        the map CRS is changed
        """
        oldCrs = self.crs()
        newCrs = self.iface.mapCanvas().mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(oldCrs, newCrs)

        newCenter=transform.transform(self.center)
        newExtent=transform.transform(self.extent())

        # transform the parameters except rotation
        # TODO rotation could be better handled (maybe check rotation between old and new extent)
        # but not really worth the effort ?
        self.setCrs(newCrs)
        self.setCenter(newCenter)
        self.resetScale(newExtent.width(), newExtent.height())
        self.commitTransformParameters()

    def setupEvents(self):
        layerId=self.id()

        def removeCrsChangeHandler(layerIds):
            if layerId in layerIds:
                try:self.iface.mapCanvas().destinationCrsChanged.disconnect(self.resetTransformParametersToNewCrs)
                except:pass
                try:QgsMapLayerRegistry.instance().disconnect(removeCrsChangeHandler)
                except:pass

        self.iface.mapCanvas().destinationCrsChanged.connect(self.resetTransformParametersToNewCrs)
        QgsMapLayerRegistry.instance().layersRemoved.connect(removeCrsChangeHandler)

    def setupCrs(self):
        mapCrs=self.iface.mapCanvas().mapSettings().destinationCrs()
        self.setCrs(mapCrs)

        self.setupEvents()

    def repaint(self):
        self.emit(SIGNAL("repaintRequested()"))

    def transformParameters(self):
        return (self.center, self.rotation, self.xScale, self.yScale)

    def initializeLayer(self, screenExtent=None):
        if self.error or self.initialized or self.initializing:
            return

        if self.filepath != None:
            # not safe...
            self.initializing = True
            filepath = self.getAbsoluteFilepath()

            if not os.path.exists(filepath):
                # TODO integrate with BadLayerHandler ?
                loadErrorDialog = LoadErrorDialog(filepath)
                result = loadErrorDialog.exec_()
                if result == 1:
                    # aboslute
                    filepath = loadErrorDialog.lineEditImagePath.text()
                    # to relative if needed
                    self.filepath = utils.toRelativeToQGS(filepath)
                    self.setCustomProperty("filepath", self.filepath)
                    QgsProject.instance().dirty(True)
                else:
                    self.error = True

                del loadErrorDialog


            reader = QImageReader(filepath)
            self.image = reader.read()
            self.initialized = True
            self.initializing = False

            if screenExtent:
                # constructor called from AddLayer action
                # if not, layer loaded from QGS project file
                self.setCenter(screenExtent.center())
                self.setRotation(0.0)

                sw = screenExtent.width()
                sh = screenExtent.height()

                self.resetScale(sw, sh)

                self.commitTransformParameters()

            self.setupCrs()

    def resetScale(self, sw, sh):
        if self.useScale:
            meter_per_inch = 0.0254
            wratio = self.scale*meter_per_inch/self.dpi
            hratio = self.scale*meter_per_inch/self.dpi
        else:
            iw = self.image.width()
            ih = self.image.height()
            wratio = sw / iw
            hratio = sh / ih

        if wratio > hratio:
            # takes all height of current extent
            self.setScale(hratio, hratio)
        else:
            # all width
            self.setScale(wratio, wratio)


    def getAbsoluteFilepath(self):
        if not os.path.isabs(self.filepath):
            # relative to QGS file
            qgsPath = QgsProject.instance().fileName()
            qgsFolder, _ = os.path.split(qgsPath)
            filepath = os.path.join(qgsFolder, self.filepath)
        else:
            filepath = self.filepath

        return filepath

    def extent(self):
        self.initializeLayer()
        if not self.initialized:
            qDebug("Not Initialized")
            return QgsRectangle(0, 0, 1, 1)

        if self._extent:
            return self._extent

        topLeft, topRight, bottomRight, bottomLeft = self.cornerCoordinates()

        left = min(topLeft.x(), topRight.x(), bottomRight.x(), bottomLeft.x())
        right = max(topLeft.x(), topRight.x(), bottomRight.x(), bottomLeft.x())
        top = max(topLeft.y(), topRight.y(), bottomRight.y(), bottomLeft.y())
        bottom = min(topLeft.y(), topRight.y(), bottomRight.y(), bottomLeft.y())

        # recenter + create rectangle
        self._extent = QgsRectangle(left, bottom, right, top)
        return self._extent

    def cornerCoordinates(self):
        return self.transformedCornerCoordinates(self.center,
                                                 self.rotation, self.xScale, self.yScale)

    def transformedCornerCoordinates(self, center, rotation, xScale, yScale):
        # scale
        topLeft = QgsPoint(-self.image.width() / 2.0 * xScale,
                           self.image.height() / 2.0 * yScale)
        topRight = QgsPoint(self.image.width() / 2.0 * xScale,
                           self.image.height() / 2.0 * yScale)
        bottomLeft = QgsPoint(-self.image.width() / 2.0 * xScale,
                           - self.image.height() / 2.0 * yScale)
        bottomRight = QgsPoint(self.image.width() / 2.0 * xScale,
                               - self.image.height() / 2.0 * yScale)

        # rotate
        # minus sign because rotation is CW in this class and Qt)
        rotationRad = -rotation * math.pi / 180
        cosRot = math.cos(rotationRad)
        sinRot = math.sin(rotationRad)

        topLeft = self._rotate(topLeft, cosRot, sinRot)
        topRight = self._rotate(topRight, cosRot, sinRot)
        bottomRight = self._rotate(bottomRight, cosRot, sinRot)
        bottomLeft = self._rotate(bottomLeft, cosRot, sinRot)

        topLeft.set(topLeft.x() + center.x(), topLeft.y() + center.y())
        topRight.set(topRight.x() + center.x(), topRight.y() + center.y())
        bottomRight.set(bottomRight.x() + center.x(), bottomRight.y() + center.y())
        bottomLeft.set(bottomLeft.x() + center.x(), bottomLeft.y() + center.y())

        return (topLeft, topRight, bottomRight, bottomLeft)

    def _rotate(self, point, cosRot, sinRot):
        return QgsPoint(point.x() * cosRot - point.y() * sinRot,
                           point.x() * sinRot + point.y() * cosRot)

    def setBlendModeByName(self, modeName):
        self.blendModeName = modeName
        blendMode = getattr(QPainter, "CompositionMode_" + modeName, 0)
        self.setBlendMode(blendMode)
        self.setCustomProperty("blendMode", modeName)

    def setTransparency(self, transparency):
        self.transparency = transparency
        self.setCustomProperty("transparency", transparency)

    def draw(self, renderContext):
        if renderContext.extent().isEmpty():
            qDebug("Drawing is skipped because map extent is empty.")
            return True

        self.initializeLayer()
        if not self.initialized:
            qDebug("Drawing is skipped because nothing to draw.")
            return True

        painter = renderContext.painter()
        painter.save()
        self.prepareStyle(painter)
        self.drawRaster(renderContext)
        painter.restore()

        return True

    def drawRaster(self, renderContext):
        painter = renderContext.painter()
        self.map2pixel = renderContext.mapToPixel()

        scaleX = self.xScale / self.map2pixel.mapUnitsPerPixel()
        scaleY = self.yScale / self.map2pixel.mapUnitsPerPixel()

        rect = QRectF(QPointF(-self.image.width() / 2.0,
                            - self.image.height() / 2.0),
                     QPointF(self.image.width() / 2.0 ,
                            self.image.height() / 2.0))
        mapCenter = self.map2pixel.transform(self.center)

        # draw the image on the map canvas
        painter.translate(QPoint(round(mapCenter.x()), round(mapCenter.y())))
        painter.rotate(self.rotation)
        painter.scale(scaleX, scaleY)
        painter.drawImage(rect, self.image)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QColor(0, 0, 0));
        painter.drawRect(rect);

    def prepareStyle(self, painter):
        painter.setOpacity(1.0 - self.transparency / 100.0)

    def readXml(self, node):
        self.readCustomProperties(node)
        self.title = self.customProperty("title", "")
        self.filepath = self.customProperty("filepath", "")
        self.xScale = float(self.customProperty("xScale", 1.0))
        self.yScale = float(self.customProperty("yScale", 1.0))
        self.rotation = float(self.customProperty("rotation", 0.0))
        xCenter = float(self.customProperty("xCenter", 0.0))
        yCenter = float(self.customProperty("yCenter", 0.0))
        self.center = QgsPoint(xCenter, yCenter)
        self.setTransparency(int(self.customProperty("transparency", LayerDefaultSettings.TRANSPARENCY)))
        self.setBlendModeByName(self.customProperty("blendMode", LayerDefaultSettings.BLEND_MODE))
        return True

    def writeXml(self, node, doc):
        element = node.toElement();
        element.setAttribute("type", "plugin")
        element.setAttribute("name", FreehandRasterGeoreferencerLayer.LAYER_TYPE);
        return True

    def metadata(self):
        lines = []
        fmt = u"%s:\t%s"
        lines.append(fmt % (self.tr("Title"), self.title))
        filepath = self.getAbsoluteFilepath()
        filepath = os.path.normpath(filepath)
        lines.append(fmt % (self.tr("Path"), filepath))
        lines.append(fmt % (self.tr("Rotation (CW)"), str(self.rotation)))
        lines.append(fmt % (self.tr("X center"), str(self.center.x())))
        lines.append(fmt % (self.tr("Y center"), str(self.center.y())))
        lines.append(fmt % (self.tr("X scale"), str(self.xScale)))
        lines.append(fmt % (self.tr("Y scale"), str(self.yScale)))

        return "\n".join(lines)

    def log(self, msg):
        qDebug(msg)

    def dump(self, detail=False, bbox=None):
        pass

    def showStatusMessage(self, msg, timeout):
        self.iface.mainWindow().statusBar().showMessage(msg, timeout)

    def showBarMessage(self, title, text, level, duration):
        self.iface.messageBar().pushMessage(title, text, level, duration)

    def transparencyChanged(self, val):
        QgsProject.instance().dirty(True)
        self.setTransparency(val)
        self.emit(SIGNAL("repaintRequested()"))


class FreehandRasterGeoreferencerLayerType(QgsPluginLayerType):
    def __init__(self, plugin):
        QgsPluginLayerType.__init__(self, FreehandRasterGeoreferencerLayer.LAYER_TYPE)
        self.plugin = plugin

    def createLayer(self):
        return FreehandRasterGeoreferencerLayer(self.plugin, None, "", None, False, None, None)

    def showLayerProperties(self, layer):
        from propertiesdialog import PropertiesDialog
        dialog = PropertiesDialog(layer)
        dialog.horizontalSlider_Transparency.valueChanged.connect(layer.transparencyChanged)
        dialog.spinBox_Transparency.valueChanged.connect(layer.transparencyChanged)

        dialog.exec_()

        dialog.horizontalSlider_Transparency.valueChanged.disconnect(layer.transparencyChanged)
        dialog.spinBox_Transparency.valueChanged.disconnect(layer.transparencyChanged)
        return True
