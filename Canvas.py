from PyQt5.QtCore import QDir, Qt,QSize,QSettings,pyqtSignal,QPointF,pyqtSignal
from PyQt5.QtGui import QImage, QPainter, QPalette, QPixmap, QPen,QFont,QCursor
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,QToolBar,
        QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy,QWidget,QVBoxLayout,QTreeView)
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter

from osgeo import gdal
from PIL import Image, ImageQt
import random
import numpy as np
import time 
from decimal import Decimal
from Objects.Shape import Shape
from Objects.Lane import Shape
import math
from Lib import distance 
import pyclipper
CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor
CURSOR_TRAJECTORY_CREATION=Qt.PointingHandCursor

import matplotlib.pyplot as plt
from shapely.geometry.polygon import LinearRing


class Canvas(QWidget):
    zoomRequest = pyqtSignal(int)
    scrollRequest = pyqtSignal(int, int)
    selectionChanged = pyqtSignal(bool)
    DOTTED,SOLID=range(2)

    def __init__(self,np_array,newWidth,newHeight,resizeFactorWidth,resizeFactorHeight,geotiffScale):
        super(Canvas, self).__init__()
        im8 = Image.fromarray(np_array)
        imQt = QImage(ImageQt.ImageQt(im8))
        
        self.current=None
        self.shapes={}
        self.geotiffScale=geotiffScale
        self.resizeFactorWidth=resizeFactorWidth
        self.resizeFactorHeight=resizeFactorHeight
        self.PixMap=QPixmap.fromImage(imQt).scaled(newWidth, newHeight)
        self.drawing=False
        self.scaleFactor=1
        self.LaneUsingTrajectory=False
        self.currentLeft=None
        self.currentRight=None
        self._painter = QPainter()
        self.hVertex=None
        self.font_size=11
        self.selectedShape=None
        self.selectedShapeCopy=None
        self.currentImage=None
        self.epsilon=11
        self.Ruler=None
        self.Preview=None
        self.Trajectory=None
        self.visible = {}
        self.draggableIndex=None
        self.draggablePoint=None
        self._hideBackround = False
        self.hideBackround = False
        self.hShape=None
        self.update()
        self.repaint()

        self.imageSignal = QImage("./static/signal.png")
        self.imageStopSign=QImage("./static/stop.png")
        self.imageStopSignSmall=QImage("./static/stopSmall.png")
        mainLayout = QVBoxLayout()
        

        toolbar = QToolBar()
        mainLayout.addWidget(toolbar)

        self.deletePoint = toolbar.addAction("Delete Point", self.DeletePointFunc)
        self.deleteLane = toolbar.addAction("Delete Object", self.DeleteLaneFunc)
        self.deleteStopSign=toolbar.addAction("Detele Stop sign",self.DeleteStopSignFunc)
        self.AddFlag=toolbar.addAction("Add Flag",self.AddFlagFunc)
        self.AddTurnLeft=toolbar.addAction("Add Turn Left",self.AddTurnLeftFunc)
        self.AddTurnRight=toolbar.addAction("Add Turn Rught",self.AddTurnRightFunc)
        self.SetDottedBorder=toolbar.addAction("Set Dotted Border",self.SetDottedBorderFunc)
        self.SetSolidBorder=toolbar.addAction("Set Solid Border",self.SetSolidBorderFunc)
        self.popMenu = QMenu(self)
        self.popMenu.addAction(self.deletePoint)
        self.popMenu.addAction(self.deleteLane)
        self.popMenu.addAction(self.deleteStopSign)
        self.popMenu.addAction(self.AddFlag)
        self.popMenu.addAction(self.AddTurnLeft)
        self.popMenu.addAction(self.AddTurnRight)
        self.popMenu.addAction(self.SetDottedBorder)
        self.popMenu.addAction(self.SetSolidBorder)

        self.rightClickPos=-1
    

    def AddTurnLeftFunc(self):
        for key,shape in self.shapes.items():
            index = shape.nearestVertex(self.rightClickPos, self.epsilon/self.scaleFactor)
            if index is not None:
                shape.turn=2

    def AddTurnRightFunc(self):
        for key,shape in self.shapes.items():
            index = shape.nearestVertex(self.rightClickPos, self.epsilon/self.scaleFactor)
            if index is not None:
                shape.turn=3

    def AddFlagFunc(self):
        for key,shape in self.shapes.items():
            index = shape.nearestVertex(self.rightClickPos, self.epsilon/self.scaleFactor)
            if index is not None:
                shape.LaneChange=False
                
    def DeleteStopSignFunc(self):
        for key,shape in self.shapes.items():
            index = shape.nearestVertex(self.rightClickPos, self.epsilon/self.scaleFactor)
            if index is not None and shape.isStopSign:
                shape.isStopSign=False
                self.update()
                break

    def DeletePointFunc(self):
        for key,shape in self.shapes.items():
            index = shape.nearestVertex(self.rightClickPos, self.epsilon/self.scaleFactor)
            if index is not None:
                borderLeft=key.find("Left")
                borderRight=key.find("Right")
                if borderLeft!=-1:
                    label=key[:borderLeft]
                    del self.shapes[label+"Right"].points[index:index+1]
                elif borderRight!=-1:
                    label=key[:borderRight]
                    del self.shapes[label+"Left"].points[index:index+1]
                del self.shapes[key].points[index:index+1]
                break
        self.update()
    def SetDottedBorderFunc(self):
        for key,shape in self.shapes.items():
            index = shape.nearestVertex(self.rightClickPos, self.epsilon/self.scaleFactor)
            if index is not None:
                shape.type=Shape.DOTTED_WHITE


    def SetSolidBorderFunc(self):
        for key,shape in self.shapes.items():
            index = shape.nearestVertex(self.rightClickPos, self.epsilon/self.scaleFactor)
            if index is not None:
                shape.type=Shape.SOLID_WHITE


    def DeleteLaneFunc(self):
        key1=0
        for key,shape in self.shapes.items():
            index = shape.nearestVertex(self.rightClickPos, self.epsilon/self.scaleFactor)
            if index is not None:
                borderLeft=key.find("Left")
                borderRight=key.find("Right")
                lane=key.find("lane")
                st=key.find("stoplane")
                if borderLeft!=-1:
                    label=key[:borderLeft]
                    del self.shapes[label+"Left"]
                    del self.shapes[label]
                    del self.shapes[label+"Right"]
                elif borderRight!=-1:
                    label=key[:borderRight]
                    del self.shapes[label+"Right"]
                    del self.shapes[label]
                    del self.shapes[label+"Left"]
                elif lane!=-1 and st==-1:
                    del self.shapes[key+"Right"]
                    del self.shapes[key+"Left"]
                    del self.shapes[key]
                else:
                    del self.shapes[key]
                break
 
        self.draggableIndex=None
        self.draggablePoint=None
        self.update()
    def addPoints(self,shape):
        isAdded=False
        for i in range(0,len(shape.points)-1):
            print(self.distance_between(shape.points[i],shape.points[i+1]))
            if self.distance_between(shape.points[i],shape.points[i+1])>70:
                x=(shape.points[i].x()+shape.points[i+1].x())/2
                y=(shape.points[i].y()+shape.points[i+1].y())/2
                newPoint=QPointF(x,y)
                shape.points.insert(i+1,newPoint)
                isAdded=True
        if isAdded:
            self.addPoints(shape)


    def getBezierCurve (self,arr=None):
        isPrew=True
        if arr is None:
            isPrew=False
            arr=self.current.points
      
        step = 20
        res=[]
        res.append(self.current.points[0])
        step=int((float(step)/self.distance_between(arr[0],arr[2])))
        if step==0:
            step=1
 
        for t in range(0, 20 , step):
            k=float(t/20)

            res.append(QPointF(0,0))
            for i in range(0, len(arr), 1):
                b = self.getBezierBasis(i, len(arr) - 1, k)
                res[-1].setX(res[-1].x()+arr[i].x() * b)
                res[-1].setY(res[-1].y()+arr[i].y() * b)
        res.append(self.current.points[-1])
        if not isPrew:
            self.current.points=res
            self.update()
            return self.current.points
        else:
            return res

    def getBezierBasis(self,i, n, t):
        def f(n):
            if n <= 1:
                return 1
            else:
                return n*f(n-1)
        return (f(n) / (f(i) * f(n - i))) * (t**i) * ((1 - t)**(n - i))
    def distance_between(self,p1,p2):
        return math.sqrt(math.pow(p2.x()-p1.x(),2)+math.pow(p2.y()-p1.y(),2))
    def FindEdgeLanes(self,point):
        newpoint=QPointF(0,0)
        distance=1000
        isStart=False
        Id=""
        for el,shape in self.shapes.items():
            if el.find("Left")==-1 and el.find("Right")==-1 and el.find("lane")!=-1: 
                distFirst=self.distance_between(shape.points[0],point)
                distLast=self.distance_between(shape.points[-1],point)
                if distFirst<distance:
                    newpoint=shape.points[0]
                    distance=distFirst
                    Id=el
                    isStart=True
                if distLast<distance:
                    newpoint=shape.points[-1]
                    distance=distLast
                    Id=el
                    isStart=False
        if isStart:
            secpoint=self.shapes[Id].points[0]
            thirdpoint=self.shapes[Id].points[1]
        else:
            secpoint=self.shapes[Id].points[-1]
            thirdpoint=self.shapes[Id].points[-2]

        finalPointsX=newpoint.x()
        finalPointsY=newpoint.y()
        newpointTwo=QPointF(finalPointsX,finalPointsY)
        if distance>150:
            return -1,-1
        else:
            return [newpointTwo,Id,secpoint]

    def drawPolyline(self):
        painter = QPainter()
        painter.begin()
        pen = QPen(Qt.red)
        pen.setWidth(200)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.drawPoint(300, 300)
        painter.drawLine(100, 100, 4000, 4000)
        painter.end()
    def GetCurveBezier(self):
        pass
    def SetStopSign(self):
        pass
    def drawBorders(self):
        pass
    def setScale(self,scale):
        self.scaleFactor=scale
        for key,shape in self.shapes.items():
            shape.scale=scale

    def mouseMoveEvent(self, ev):
        pos=ev.pos()/self.scaleFactor


        for key,shape in self.shapes.items():
            index = shape.nearestVertex(pos, self.epsilon/self.scaleFactor)
            if index is None and self.draggableIndex==key:
                index = shape.nearestVertex(pos, self.epsilon/self.scaleFactor*3)
                if index!=self.draggablePoint:
                    index=None
            if self.draggableIndex is not None and key!=self.draggableIndex:
                continue
            if index is not None:
                if index!= self.draggablePoint and self.draggablePoint is not None:
                    index=self.draggablePoint
                self.drag(index,shape,key)
                break
            else:
                self.drawing=True
                self.draggableIndex=None
                self.draggablePoint=None    

        else:  # Nothing found, clear highlights, reset state.
            if self.hShape:
                self.hShape.highlightClear()
                self.update()
            self.hVertex, self.hShape = None, None
        

        # Polygon/Vertex moving.
        if Qt.LeftButton & ev.buttons():
            if self.selectedVertex():
                self.boundedMoveVertex(pos)
                self.repaint()
          
            return

    def drag(self,index,shape,key):
       
        self.drawing=False
        if self.selectedVertex():
            self.hShape.highlightClear()
        self.hVertex, self.hShape = index, shape
        self.draggableIndex=key
        self.draggablePoint=index
        shape.highlightVertex(index, shape.MOVE_VERTEX)
        self.overrideCursor(CURSOR_POINT)
        self.setToolTip("Click & drag to move point")
        self.setStatusTip(self.toolTip())
        self.update()
    def FindClosestPoint(self,pos):
        point=min(self.Trajectory, key=lambda x:self.distance_between(x,pos))

        if self.distance_between(point,pos)<6:
            return point
        else:
            return None

        

    def boundedMoveVertex(self, pos):
        index, shape = self.hVertex, self.hShape
        point = shape[index]
        shiftPos = (pos - point)
        shape.moveVertexBy(index, shiftPos)
      
    def convert(self, p, p2, distanceX,distanceY, use_first=True):
        delta_y = p2.y() - p.y()
        delta_x = p2.x() - p.x()
        if use_first:
            point = p
        else:
            point = p2

        left_angle = math.atan2(delta_y, delta_x) + math.pi / 2.0
        right_angle = math.atan2(delta_y, delta_x) - math.pi / 2.0

        lp =QPointF((point.x() + (math.cos(left_angle) * distanceX)),(point.y() + (math.sin(left_angle) * distanceY)))

        rp = QPointF((point.x() + (math.cos(right_angle) * distanceX)),(point.y() + (math.sin(right_angle) * distanceY)))
     
        return lp, rp
    def signToStopLane(self,idStopLane):
        if idStopLane!=" ":
            self.shapes[idStopLane].isStopSign=True
            self.update()

    def createBorder(self,width):
        offsetX=float((Decimal(width/2)/Decimal(self.geotiffScale)/self.resizeFactorWidth))
        offsetY=float(Decimal(width/2)/Decimal(self.geotiffScale)/self.resizeFactorHeight)

        if self.currentLeft is None:
            self.currentLeft=Shape()
            self.currentRight=Shape()
        for i in range(1,len(self.current.points)):
            pos=self.current.points[i] 
            pos2=self.current.points[i-1]
            lp,rp=self.convert(pos2, pos, offsetX,offsetY, use_first=(i != len(self.current.points) - 1))
            self.currentRight.addPoint(rp)
            self.currentLeft.addPoint(lp)
        if len(self.current.points)==2:
            pos=self.current.points[0]
            pos2=self.current.points[1]
            lp,rp=self.convert(pos2, pos, offsetX,offsetY, use_first=(i != len(self.current.points) - 1))
            self.currentRight.addPoint(lp)
            self.currentLeft.addPoint(rp)

        return self.currentLeft,self.currentRight
    def  intersectionLanes(self,stopLane,lane):
        stPoints=[[stopLane.points[0].x(),stopLane.points[0].y()],[stopLane.points[1].x(),stopLane.points[1].y()]]
        for i  in range(1,len(lane.points)):
            fragment=[[lane.points[i-1].x(),lane.points[i-1].y()],[lane.points[i].x(),lane.points[i].y()]]
            xdiff = (fragment[i-1][0]- fragment[i][0], stPoints[0][0]- stPoints[1][0])
            ydiff = (fragment[i-1][1] - fragment[i][1], stPoints[0][1] - stPoints[1][1]) #Typo was here

            def det(a, b):
                return a[0] * b[1] - a[1] * b[0]

            div = det(xdiff, ydiff)
            if div == 0:
                return None

            d = (det(*fragment), det(*stPoints))
            x = det(d, xdiff) / div
            y = det(d, ydiff) / div
            return QPointF(x, y)
    def AddPointsBeetween(self,pointStart,pointFinish):
        try:
            indexStart=self.Trajectory.points.index(pointStart)
        except:
            pointStart=self.FindClosestPoint(pointStart)
            indexStart=self.Trajectory.points.index(pointStart)
        try:
            indexFinish=self.Trajectory.points.index(pointFinish)
        except:
            pointFinish=self.FindClosestPoint(pointFinish)
            indexFinish=self.Trajectory.points.index(pointFinish)
        return self.Trajectory.points[indexStart:indexFinish]
    def setHiding(self, enable=True):
        self._hideBackround = self.hideBackround if enable else False
    def mousePressEvent(self, event):

        pos=event.pos()/self.scaleFactor


        if event.button() == Qt.LeftButton:
            if self.Ruler is not None :
                if len(self.Ruler.points)>=2:
                    self.Ruler.points=[]
                self.Ruler.addPoint(pos)
                    
            elif self.drawing:
                if self.LaneUsingTrajectory==True:
                    point=self.FindClosestPoint(pos)

                    if point is not None:
                        if len(self.current.points)==0 or len(self.current.points)>1:
                            self.current.points.clear()
                            self.current.addPoint(point)
                        
                        else:
                            self.current.points=self.AddPointsBeetween(self.current.points[0],point)


                elif  self.current is not None and self.current.shape_type==self.current.LANE:
                        self.current.addPoint(pos)
                elif  self.current is not None and self.current.shape_type==self.current.JUNCTION:
                    if len(self.current.points)<3:
                        self.current.addPoint(pos)
                    else:
                        self.setToolTip("Only three points")
                        #Error             
                        #self.finalise()
                elif  self.current is not None and self.current.shape_type==self.current.STOPLANE: 
                    if len(self.current.points)<2:
                        self.current.addPoint(pos)
                    else:
                        self.setToolTip("Only two points")
                elif self.currentImage is not None and self.currentImage.shape_type==self.currentImage.SIGNAL:
                    if len(self.currentImage.points)==0:
                        self.currentImage.addPoint(pos)



                self.repaint()
                self.update()
                pass
            else:
                self.prevPoint = pos
                self.repaint()            
       
            
          
            self.repaint()
            self.lastPoint = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        pos=event.pos()/self.scaleFactor 
        if event.button() == Qt.LeftButton:
            pass
        if event.button()==Qt.RightButton:
            cursor =QCursor()
            self.rightClickPos=pos
            self.popMenu.exec_(cursor.pos())

    def paintEvent(self, event):

        if not self.PixMap:
            return super(Canvas, self).paintEvent(event)

        
        p = self._painter
        p.begin(self)
        p.setFont(QFont('Times', self.font_size, QFont.Bold))
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scaleFactor, self.scaleFactor)
        p.drawPixmap(0, 0, self.PixMap)
        
        
            # painter.setPen(QPen(Qt.red, 30, Qt.SolidLine))
            #painter.drawLine(self.lastPoint/self.scaleFactor, event.pos()/self.scaleFactor)
            #painter.setRenderHint(QPainter.Antialiasing)
            #painter.setRenderHint(QPainter.HighQualityAntialiasing)
            #painter.setRenderHint(QPainter.SmoothPixmapTransform)
            # self.current.paint(painter) 
        if self.Preview is not None:
            self.Preview.paint(p)
        if self.Trajectory is not None:
            self.Trajectory.paint(p)
        if self.Ruler is not None and len(self.Ruler.points)>0:
            self.Ruler.scale=self.scaleFactor
            if len(self.Ruler.points)==2:
                x1=float(Decimal(self.Ruler.points[0].x())*Decimal(self.geotiffScale)*self.resizeFactorWidth)
                y1=float(Decimal(self.Ruler.points[0].y())*Decimal(self.geotiffScale)*self.resizeFactorHeight)
                x2=float(Decimal(self.Ruler.points[1].x())*Decimal(self.geotiffScale)*self.resizeFactorWidth)
                y2=float(Decimal(self.Ruler.points[1].y())*Decimal(self.geotiffScale)*self.resizeFactorHeight)
                distance=str(round(float(self.distance_between(QPointF(x1,y1),QPointF(x2,y2))),2))
            else:
                distance="0"
            self.Ruler.paint(p,distance=distance)
        if self.current is not None:
            self.current.scale = self.scaleFactor
        if self.currentLeft is not None:
            self.currentLeft.scale = self.scaleFactor
        if self.currentRight is not None:
            self.currentRight.scale = self.scaleFactor

        for key,shape in self.shapes.items():
                if len(shape.points)!=0:
                    if key.find("signal")!=-1:
                        shape.paint(p,self.imageSignal.scaled(15/self.scaleFactor, 40/self.scaleFactor, Qt.KeepAspectRatio))
                    if shape.isStopSign:
                        if 40/self.scaleFactor<10:
                            shape.paint(p,self.imageStopSignSmall)
                        else:
                             shape.paint(p,self.imageStopSign.scaled(40/self.scaleFactor, 40/self.scaleFactor))
                            
                    else:
                       shape.paint(p)     
 
        p.end()
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.PixMap:
            res=(self.scaleFactor * (self.PixMap.size()))

            return res
        return super(Canvas, self).minimumSizeHint()


    def isVisible(self, shape):
        return self.visible.get(shape, True)
    def setShapeVisible(self, shape, value):
        self.visible[shape] = value
        self.repaint()
    def setDrawing(self,mode):
        self.drawing=mode
    def selectedVertex(self):
        return self.hVertex is not None
    def overrideCursor(self, cursor):
        self.restoreCursor()
        self._cursor = cursor
        if not self.LaneUsingTrajectory:
            QApplication.setOverrideCursor(cursor)
    def restoreCursor(self):
        if not self.LaneUsingTrajectory:
            QApplication.restoreOverrideCursor()
