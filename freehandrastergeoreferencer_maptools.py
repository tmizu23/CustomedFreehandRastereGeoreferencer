from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import math
from operator import itemgetter
from rastershadowmapcanvasitem import RasterShadowMapCanvasItem

class MoveRasterMapTool(QgsMapToolEmitPoint):
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        
        self.rasterShadow = RasterShadowMapCanvasItem(self.canvas)
        
        self.rubberBandDisplacement = QgsRubberBand(self.canvas, QGis.Line)
        self.rubberBandDisplacement.setColor(Qt.red)
        self.rubberBandDisplacement.setWidth(1)
        
        self.rubberBandExtent = QgsRubberBand(self.canvas, QGis.Line)
        self.rubberBandExtent.setColor(Qt.red)
        self.rubberBandExtent.setWidth(1)
        
        self.isLayerVisible = True
        
        self.reset()
        
    def setLayer(self, layer):
        self.layer = layer

    def undo(self):
        x = self.undoX
        y = self.undoY
        self.layer.setCenter(QgsPoint(x, y))
        self.iface.legendInterface().setLayerVisible(self.layer, self.isLayerVisible)
        self.layer.repaint()
        self.layer.commitTransformParameters()

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBandDisplacement.reset(QGis.Line)
        self.rubberBandExtent.reset(QGis.Line)
        self.rasterShadow.reset()
        self.layer = None

    def canvasPressEvent(self, e):
        self.startPoint = self.toMapCoordinates(e.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        self.originalCenter = self.layer.center
        self.undoX = self.originalCenter.x()
        self.undoY = self.originalCenter.y()
        # this tool do the displacement itself TODO update so it is done by transformed coordinates + new center)
        self.originalCornerPoints = self.layer.transformedCornerCoordinates(*self.layer.transformParameters())
        
        self.isLayerVisible = self.iface.legendInterface().isLayerVisible(self.layer)
        self.iface.legendInterface().setLayerVisible(self.layer, False)
        
        self.showDisplacement(self.startPoint, self.endPoint)
        #QgsMessageLog.logMessage("{},{}".format(self.undoX,self.undoY), "debug",QgsMessageLog.INFO)

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        
        self.rubberBandDisplacement.reset(QGis.Line)
        self.rubberBandExtent.reset(QGis.Line)
        self.rasterShadow.reset()
        
        x = self.originalCenter.x() + self.endPoint.x() - self.startPoint.x()
        y = self.originalCenter.y() + self.endPoint.y() - self.startPoint.y()
        self.layer.setCenter(QgsPoint(x,y))
        
        self.iface.legendInterface().setLayerVisible(self.layer, self.isLayerVisible)
        self.layer.repaint()
        
        self.layer.commitTransformParameters()

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return

        self.endPoint = self.toMapCoordinates(e.pos())
        self.showDisplacement(self.startPoint, self.endPoint)

    def showDisplacement(self, startPoint, endPoint):      
        self.rubberBandDisplacement.reset(QGis.Line)
        point1 = QgsPoint(startPoint.x(), startPoint.y())
        point2 = QgsPoint(endPoint.x(), endPoint.y())
        self.rubberBandDisplacement.addPoint(point1, False)
        self.rubberBandDisplacement.addPoint(point2, True)  # true to update canvas
        self.rubberBandDisplacement.show()
        
        self.rubberBandExtent.reset(QGis.Line)
        for point in self.originalCornerPoints:
            self._addDisplacementToPoint(self.rubberBandExtent, point, False)
        # for closing
        self._addDisplacementToPoint(self.rubberBandExtent, self.originalCornerPoints[0], True)
        self.rubberBandExtent.show()
        
        self.rasterShadow.reset(self.layer)
        self.rasterShadow.setDeltaDisplacement(self.endPoint.x() - self.startPoint.x(), self.endPoint.y() - self.startPoint.y(), True)
        self.rasterShadow.show()
        
    def _addDisplacementToPoint(self, rubberBand, point, doUpdate):
        x = point.x() + self.endPoint.x() - self.startPoint.x()
        y = point.y() + self.endPoint.y() - self.startPoint.y()
        self.rubberBandExtent.addPoint(QgsPoint(x, y), doUpdate)

# move the mouse in the Y axis to rotate
class RotateRasterMapTool(QgsMapToolEmitPoint):
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        
        self.rasterShadow = RasterShadowMapCanvasItem(self.canvas)
        
        self.rubberBandExtent = QgsRubberBand(self.canvas, QGis.Line)
        self.rubberBandExtent.setColor(Qt.red)
        self.rubberBandExtent.setWidth(1)
        
        self.reset()
        
    def setLayer(self, layer):
        self.layer = layer

    def undo(self):
        rotation = -1.0*self.undoRotation
        self.undoRotation = 0 #undo is only one time
        self.layer.setRotation(self.layer.rotation + rotation)
        self.iface.legendInterface().setLayerVisible(self.layer, self.isLayerVisible)
        self.layer.repaint()
        self.layer.commitTransformParameters()
        QgsMessageLog.logMessage("{}".format(rotation), "test", QgsMessageLog.INFO)

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBandExtent.reset(QGis.Line)
        self.rasterShadow.reset()
        self.layer = None

    def canvasPressEvent(self, e):
        self.startY = e.pos().y()
        self.endY = self.startY
        self.isEmittingPoint = True
        self.height = self.canvas.height()
        
        self.isLayerVisible = self.iface.legendInterface().isLayerVisible(self.layer)
        self.iface.legendInterface().setLayerVisible(self.layer, False)
        
        rotation = self.computeRotation()
        self.showRotation(rotation)
        

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        
        self.rubberBandExtent.reset(QGis.Line)
        self.rasterShadow.reset()
        
        rotation = self.computeRotation()
        self.undoRotation = rotation
        self.layer.setRotation(self.layer.rotation + rotation)
        
        self.iface.legendInterface().setLayerVisible(self.layer, self.isLayerVisible)
        self.layer.repaint()
        
        self.layer.commitTransformParameters()

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return

        self.endY = e.pos().y()
        rotation = self.computeRotation()
        self.showRotation(rotation)
        
    def computeRotation(self):
        dY = self.endY - self.startY
        return 90.0 * dY / self.height

    def showRotation(self, rotation):
        center, originalRotation, xScale, yScale = self.layer.transformParameters()
        newRotation = rotation + originalRotation
        cornerPoints = self.layer.transformedCornerCoordinates(center, newRotation, xScale, yScale)
        
        self.rubberBandExtent.reset(QGis.Line)
        for point in cornerPoints:
            self.rubberBandExtent.addPoint(point, False)
        # for closing
        self.rubberBandExtent.addPoint(cornerPoints[0], True)
        self.rubberBandExtent.show()
        
        self.rasterShadow.reset(self.layer)
        self.rasterShadow.setDeltaRotation(rotation, True)
        self.rasterShadow.show()

       
# move the map in x or y axis to scale in x or y dimensions of the imqge (no rotation
# of the coordinate system)
class ScaleRasterMapTool(QgsMapToolEmitPoint):
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        
        self.rasterShadow = RasterShadowMapCanvasItem(self.canvas)
        
        self.rubberBandExtent = QgsRubberBand(self.canvas, QGis.Line)
        self.rubberBandExtent.setColor(Qt.red)
        self.rubberBandExtent.setWidth(1)
        
        self.reset()
        
    def setLayer(self, layer):
        self.layer = layer

    def undo(self):
        xScale = 1.0/self.undoXscale
        yScale = 1.0/self.undoYscale
        self.undoXscale = 1.0 # undo is only once time
        self.undoYscale = 1.0 # undo is only once time
        self.layer.setScale(xScale * self.layer.xScale/self.undoXscale, yScale * self.layer.yScale)
        self.iface.legendInterface().setLayerVisible(self.layer, self.isLayerVisible)
        self.layer.repaint()
        self.layer.commitTransformParameters()

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBandExtent.reset(QGis.Line)
        self.rasterShadow.reset()
        self.layer = None

    def canvasPressEvent(self, e):
        self.startPoint = e.pos()
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        self.height = float(self.canvas.height())
        self.width = float(self.canvas.width())
        
        self.isLayerVisible = self.iface.legendInterface().isLayerVisible(self.layer)
        self.iface.legendInterface().setLayerVisible(self.layer, False)
        
        scaling = self.computeScaling()
        self.showScaling(*scaling)

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        
        self.rubberBandExtent.reset(QGis.Line)
        self.rasterShadow.reset()
        
        xScale, yScale = self.computeScaling()
        self.undoXscale  = xScale
        self.undoYscale = yScale
        self.layer.setScale(xScale * self.layer.xScale, yScale * self.layer.yScale)
        
        self.iface.legendInterface().setLayerVisible(self.layer, self.isLayerVisible)
        self.layer.repaint()
        
        self.layer.commitTransformParameters()

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return

        self.endPoint = e.pos()
        scaling = self.computeScaling()
        self.showScaling(*scaling)
        
    def computeScaling(self):
        dX = -(self.endPoint.x() - self.startPoint.x())
        dY = self.endPoint.y() - self.startPoint.y()
        xScale = 1.0 - (dX / (self.width * 1.1)) 
        yScale = 1.0 - (dY / (self.height * 1.1))

        scale = min(xScale, yScale)
        return (scale, scale)
        # return (xScale, yScale)

    def showScaling(self, xScale, yScale):
        if xScale == 0 and yScale == 0:
            return
        
        center, rotation, originalXScale, originalYScale = self.layer.transformParameters()
        newXScale = xScale * originalXScale
        newYScale = yScale * originalYScale
        cornerPoints = self.layer.transformedCornerCoordinates(center, rotation,newXScale, newYScale)
        
        self.rubberBandExtent.reset(QGis.Line)
        for point in cornerPoints:
            self.rubberBandExtent.addPoint(point, False)
        # for closing
        self.rubberBandExtent.addPoint(cornerPoints[0], True)
        self.rubberBandExtent.show()
        
        self.rasterShadow.reset(self.layer)
        self.rasterShadow.setDeltaScale(xScale, yScale, True)
        self.rasterShadow.show()
        
class AdjustRasterMapTool(QgsMapToolEmitPoint):
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        
        self.rasterShadow = RasterShadowMapCanvasItem(self.canvas)
        
        self.rubberBandExtent = QgsRubberBand(self.canvas, QGis.Line)
        self.rubberBandExtent.setColor(Qt.red)
        self.rubberBandExtent.setWidth(1)
        
        self.rubberBandAdjustSide = QgsRubberBand(self.canvas, QGis.Line)
        self.rubberBandAdjustSide.setColor(Qt.red)
        self.rubberBandAdjustSide.setWidth(3)
        
        self.reset()
        
    def setLayer(self, layer):
        self.layer = layer

    def undo(self):
        center = self.undoCenter
        xScale = 1.0/self.undoXscale
        yScale = 1.0/self.undoYscale
        self.undoXscale = 1.0 # undo is onle one time
        self.undoYscale = 1.0 # undo is only one time
        self.layer.setCenter(center)
        self.layer.setScale(xScale * self.layer.xScale, yScale * self.layer.yScale)

        self.iface.legendInterface().setLayerVisible(self.layer, self.isLayerVisible)
        self.layer.repaint()

        self.layer.commitTransformParameters()

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBandExtent.reset(QGis.Line)
        self.rubberBandAdjustSide.reset(QGis.Line)
        self.rasterShadow.reset()
        self.layer = None

    def canvasPressEvent(self, e):
        # find the side of the rectangle closest to the click and some data
        # necessary to compute the new cneter and scale
        topLeft, topRight, bottomRight, bottomLeft = self.layer.cornerCoordinates()
        top = [topLeft, topRight]
        right = [bottomRight, topRight]
        bottom = [bottomRight, bottomLeft]
        left = [bottomLeft, topLeft]
        
        click = QgsGeometry.fromPoint(self.toMapCoordinates(e.pos()))
        
        # order is important (for referenceSide)
        sides = [top, right, bottom, left] 
        distances = [click.distance(QgsGeometry.fromPolyline(side)) for side in sides]
        self.indexSide = self.minDistance(distances)
        self.side = sides[self.indexSide]
        self.sidePoint = self.center(self.side)
        self.vector = self.directionVector(self.side)
        # side that does not move (opposite of indexSide)
        self.referenceSide = sides[(self.indexSide + 2) % 4]
        self.referencePoint = self.center(self.referenceSide)
        self.referenceDistance = self.distance(self.sidePoint, self.referencePoint)
        self.isXScale = self.indexSide % 2 == 1
        
        self.startPoint = click.asPoint()
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        
        self.isLayerVisible = self.iface.legendInterface().isLayerVisible(self.layer)
        self.iface.legendInterface().setLayerVisible(self.layer, False)
        
        adjustment = self.computeAdjustment()
        self.undoCenter, _, _ = adjustment
        self.showAdjustment(*adjustment)
        
    def minDistance(self, distances):
        sortedDistances = [i[0] for i in sorted(enumerate(distances), key=itemgetter(1))]
        # first is min
        return sortedDistances[0]
    
    def directionVector(self, side):
        sideCenter = self.center(side)
        layerCenter = self.layer.center
        vector = [sideCenter.x() - layerCenter.x(), sideCenter.y() - layerCenter.y()]
        norm = math.sqrt(vector[0]**2 + vector[1]**2)
        normedVector = [vector[0] / norm, vector[1] / norm]
        return normedVector
    
    def center(self, side):
        return QgsPoint((side[0].x() + side[1].x()) / 2, (side[0].y() + side[1].y()) / 2)
    
    def distance(self, pt1, pt2):
        return math.sqrt((pt1.x() - pt2.x())**2 + (pt1.y() - pt2.y())**2)

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        
        self.rubberBandExtent.reset(QGis.Line)
        self.rubberBandAdjustSide.reset(QGis.Line)
        self.rasterShadow.reset()
        
        center, xScale, yScale = self.computeAdjustment()
        self.undoXscale = xScale
        self.undoYscale = yScale
        self.layer.setCenter(center)
        self.layer.setScale(xScale * self.layer.xScale, yScale * self.layer.yScale)
        
        self.iface.legendInterface().setLayerVisible(self.layer, self.isLayerVisible)
        self.layer.repaint()
        
        self.layer.commitTransformParameters()

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return
        
        self.endPoint = self.toMapCoordinates(e.pos())

        adjustment = self.computeAdjustment()
        self.showAdjustment(*adjustment)
        
    def computeAdjustment(self):
        dX = self.endPoint.x() - self.startPoint.x()
        dY = self.endPoint.y() - self.startPoint.y()
        # project on vector
        dp = dX * self.vector[0] + dY * self.vector[1]
        
        # do not go beyond 5% of the current size of side
        if dp < -0.95 * self.referenceDistance:
            dp = -0.95 * self.referenceDistance
        
        updatedSidePoint = QgsPoint(self.sidePoint.x() + dp * self.vector[0],
                                    self.sidePoint.y() + dp * self.vector[1])
        
        center = self.center([self.referencePoint, updatedSidePoint])
        scaleFactor = self.distance(self.referencePoint, updatedSidePoint)
        if self.isXScale:
            xScale = scaleFactor / self.referenceDistance
            yScale = 1.0
        else:
            xScale = 1.0
            yScale =  scaleFactor / self.referenceDistance
        
        return (center, xScale, yScale)

    def showAdjustment(self, center, xScale, yScale):
        _, rotation, originalXScale, originalYScale = self.layer.transformParameters()
        newXScale = xScale * originalXScale
        newYScale = yScale * originalYScale
        cornerPoints = self.layer.transformedCornerCoordinates(center, rotation, newXScale, newYScale)
        
        self.rubberBandExtent.reset(QGis.Line)
        for point in cornerPoints:
            self.rubberBandExtent.addPoint(point, False)
        # for closing
        self.rubberBandExtent.addPoint(cornerPoints[0], True)
        self.rubberBandExtent.show()
        
        # show rubberband for side
        # see def of indexSide in init:
        #cornerpoints are (topLeft, topRight, bottomRight, bottomLeft)
        self.rubberBandAdjustSide.reset(QGis.Line)
        self.rubberBandAdjustSide.addPoint(cornerPoints[self.indexSide % 4], False)
        self.rubberBandAdjustSide.addPoint(cornerPoints[(self.indexSide + 1) % 4], True)
        self.rubberBandAdjustSide.show()
        
        self.rasterShadow.reset(self.layer)
        dx = center.x() - self.layer.center.x()
        dy = center.y() - self.layer.center.y()
        self.rasterShadow.setDeltaDisplacement(dx, dy, False)
        self.rasterShadow.setDeltaScale(xScale, yScale, True)
        self.rasterShadow.show()
        
        
