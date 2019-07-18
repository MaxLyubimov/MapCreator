from PyQt5.QtCore import QDir, Qt,QSize,QSettings,QRect,QEvent
from PyQt5.QtGui import QImage, QPainter, QPalette, QPixmap, QPen,QIntValidator
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog,QLabel,QToolBar,
        QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy,QVBoxLayout,QWidget,QFrame,QScrollBar,QHBoxLayout,QTextEdit,QLineEdit,QComboBox)
import create_map as cr
from decimal import Decimal
import pickle
import os
from itertools import chain
from shapely.geometry import LineString

def delIfEmpty(self, listObj):
    counter=0
    for obj in listObj: 
        if obj.id not in self.imageLabel.shapes or len(self.imageLabel.shapes[obj.id].points)==0:
            del listObj[counter]
        counter+=1



def clearList(self):

    delIfEmpty(self,self.Lanes)
    delIfEmpty(self,self.StopLanes)
    delIfEmpty(self,self.Signals)
    delIfEmpty(self,self.Junctions)

    counter=0

    for obj in self.Neighbors:
        if not self.findById(obj.mainLane ,self.Lanes):
            del self.Neighbors[counter]
        elif obj.leftForward is not None and not  self.findById(obj.leftForward ,self.Lanes):
            del self.Neighbors[counter]
        elif obj.leftReverse is not None and not  self.findById(obj.leftReverse ,self.Lanes):
            del self.Neighbors[counter]
        elif obj.RightForward is not None and not  self.findById(obj.RightForward ,self.Lanes):
            del self.Neighbors[counter]
        elif obj.RightReverse is not None and not  self.findById(obj.RightReverse ,self.Lanes):
            del self.Neighbors[counter]
        counter+=1
    counter=0
    for rel in self.Relations:
        if not ((self.findById(rel.successor ,self.Lanes) or self.findById(rel.successor ,self.Junctions)) and  (self.findById(rel.predecessor ,self.Lanes) or self.findById(rel.predecessor,self.Junctions))):
            del self.Relations[counter]
        counter+=1
    counter=0
    for ovr in self.Overlaps:
        if not (self.findById(ovr.laneOverlapId, self.Lanes)  or  self.findById(ovr.laneOverlapId ,self.Junctions) and (self.findById(ovr.IdSecObject,self.StopSigns) or self.findById(ovr.IdSecObject,self.Signals))):
            del self.Overlaps[counter]
        
        counter+=1
    counter=0
    for obj in self.StopSigns: 
        if obj.idStopLane not in self.imageLabel.shapes or  not self.imageLabel.shapes[obj.idStopLane].isStopSign:
            del self.StopSigns[counter] 
        counter+=1
    
    for lane in self.Junctions:
        lane.points=[]
    for lane in self.Lanes:
        lane.points=[]
        lane.leftBorderPoints=[]
        lane.rightBorderPoints=[]
    for lane in self.StopLanes:
        lane.points=[]
    for ovr in self.Overlaps:
        ovr.points=[]
    for signal in self.Signals:
        signal.points=[]
    for sign in self.StopSigns:
        sign.pointsStopLane=[]
def SaveTxt(self,filename):
    clearList(self)

    with open(filename, 'wb') as f:
        pickle.dump(self.Junctions, f)
        pickle.dump(self.Lanes, f)
        pickle.dump(self.Relations, f)
        pickle.dump(self.Neighbors,f)
        pickle.dump(self.imageLabel.shapes, f)
        pickle.dump(self.StopLanes,f)
        pickle.dump(self.Overlaps,f)
        pickle.dump(self.Signals,f)
        pickle.dump(self.StopSigns,f)
    with open(self.fileSetings, 'wb') as f:
        pickle.dump((self.offsetX,self.offsetY,self.rotation),f)
    bufPoints=[]

    for obj in self.Overlaps:
        point=obj.pointOverlap
        print(point)
        Lanepoints=self.findById(obj.laneOverlapId,self.Lanes)
        if Lanepoints is None:
            Lanepoints=self.findById(obj.laneOverlapId,self.Junctions)
            shape=None
            if Lanepoints.id in self.imageLabel.shapes:
                shape=self.imageLabel.shapes[obj.id]
                if shape.LaneChange:
                    obj.laneOverlapId=obj.laneOverlapId.replace("junction","laneChange")
            else:
                continue
        Lanepoints=Lanepoints.points
        pointMap=[Decimal(point.x())*(self.resizeFactorWidth*Decimal(self.geotiffScale)),Decimal(point.y())*(self.resizeFactorHeight*Decimal(self.geotiffScale))]
        Lanepoints.insert(1, pointMap)
        line = LineString(Lanepoints[:2])
        Lanepoints.remove(pointMap)
        dist = line.length
        bufPoints.append(obj.pointOverlap)
        obj.pointOverlap=dist
    for obj in self.Relations:
        if obj.predecessor.find("junction")!=-1:
            shape=None
            if obj.predecessor in self.imageLabel.shapes:
                shape=self.imageLabel.shapes[obj.predecessor]  
                junk=self.findById(obj.predecessor,self.Junctions)
                if junk is not None and shape.LaneChange:
                    obj.predecessor=obj.predecessor.replace("junction","laneChange")
                    print(obj.predecessor)
                    #junk.id=obj.predecessor
            else:
                continue
            
        if obj.successor.find("junction")!=-1:
            shape=None
            if obj.successor in self.imageLabel.shapes:
                shape=self.imageLabel.shapes[obj.successor]
                junk=self.findById(obj.successor,self.Junctions)
                if junk is not None and shape.LaneChange:
                    obj.successor=obj.successor.replace("junction","laneChange")
                    print(obj.successor)
                    #junk.id=obj.successor
            else:
                continue
           



    for obj in self.Junctions:
        print(obj.id)
        shape=None
        if obj.id in self.imageLabel.shapes:
            shape=self.imageLabel.shapes[obj.id]
        else:
            self.Junctions.remove(obj)
            continue
        for point in shape.points:

            if type(point) is list:
                continue
            obj.points.append([Decimal(point.x())*(self.resizeFactorWidth*Decimal(self.geotiffScale)),Decimal(point.y())*(self.resizeFactorHeight*Decimal(self.geotiffScale))])
        obj.isLaneChange=shape.LaneChange
        if obj.isLaneChange:
            obj.id=obj.id.replace("junction","laneChange")
        try:
            obj.turn=shape.turn#!!!!!!!!!!!!!!
        except:
            obj.turn=1

    for obj in self.Lanes: 
        shape=None
        if obj.id in self.imageLabel.shapes:
            shape=self.imageLabel.shapes[obj.id]
        else:
            self.Lanes.remove(obj)
            continue
        shapeLeft=self.imageLabel.shapes[obj.id+"Left"]
        shapeRight=self.imageLabel.shapes[obj.id+"Right"]
        for point in shape.points:
            obj.points.append([Decimal(point.x())*(self.resizeFactorWidth*Decimal(self.geotiffScale)),Decimal(point.y())*(self.resizeFactorHeight*Decimal(self.geotiffScale))])
       
        for point in shapeLeft.points:
            obj.leftBorderPoints.append([Decimal(point.x())*(self.resizeFactorWidth*Decimal(self.geotiffScale)),Decimal(point.y())*(self.resizeFactorHeight*Decimal(self.geotiffScale))])
        for point in shapeRight.points:
            obj.rightBorderPoints.append([Decimal(point.x())*(self.resizeFactorWidth*Decimal(self.geotiffScale)),Decimal(point.y())*(self.resizeFactorHeight*Decimal(self.geotiffScale))])
        obj.leftBorderType=shapeLeft.type
        obj.rightBorderType=shapeRight.type
        try:
            obj.turn=shape.turn#!!!!!!!!!!!!!!
        except:
            obj.turn=1
    for obj in self.StopLanes:
        shape=None
        if obj.id in self.imageLabel.shapes:
            shape=self.imageLabel.shapes[obj.id]
        else:
            self.StopLanes.remove(obj)
            continue
        for point in shape.points:
            obj.points.append([Decimal(point.x())*(self.resizeFactorWidth*Decimal(self.geotiffScale)),Decimal(point.y())*(self.resizeFactorHeight*Decimal(self.geotiffScale))])
   
    
    for obj in self.Signals:
        point=None
        if obj.id in self.imageLabel.shapes or obj.idStopLane in self.imageLabel.shapes:
            point=self.imageLabel.shapes[obj.id].points[0]
            print(self.imageLabel.shapes[obj.id].points)
            print(obj.id)
        else:
            self.Signals.remove(obj)
            continue
        pointsLane=self.imageLabel.shapes[obj.idStopLane].points
        
        obj.point=[Decimal(point.x())*(self.resizeFactorWidth*Decimal(self.geotiffScale)),Decimal(point.y())*(self.resizeFactorHeight*Decimal(self.geotiffScale))]

        for point in pointsLane:
            obj.pointsStopLane.append([Decimal(point.x())*(self.resizeFactorWidth*Decimal(self.geotiffScale)),Decimal(point.y())*(self.resizeFactorHeight*Decimal(self.geotiffScale))])

    for obj in self.StopSigns:
        pointsLane=None
        if obj.idStopLane in self.imageLabel.shapes:
            pointsLane=self.imageLabel.shapes[obj.idStopLane].points
        else:
            self.StopSigns.remove(obj)
            continue
     
        for point in pointsLane:
            obj.pointsStopLane.append([Decimal(point.x())*(self.resizeFactorWidth*Decimal(self.geotiffScale)),Decimal(point.y())*(self.resizeFactorHeight*Decimal(self.geotiffScale))])
    gen=cr.BaseMapGeneration()

    gen.start(self.Lanes,self.Junctions,self.Relations,self.Neighbors,self.Overlaps,self.Signals,self.StopSigns,self.offsetX,self.offsetY,self.rotation)
    for i in range(0,len(self.Overlaps)):
        self.Overlaps[i].pointOverlap=bufPoints[i]






