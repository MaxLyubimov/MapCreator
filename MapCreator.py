
#!/usr/bin/env python




from PyQt5.QtCore import QDir, Qt,QSize,QSettings,QRect,QEvent,QFile
from PyQt5.QtGui import QImage, QPainter, QPalette, QPixmap, QPen,QIcon
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,QToolBar,
        QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy,QVBoxLayout,QWidget,QFrame,QScrollBar,QHBoxLayout,QTextEdit)
from OffsetsDialog import OffsetsDialog
from osgeo import gdal
from PIL import Image, ImageQt
import random
import numpy as np
from Canvas import Canvas
import time 
import os 
from Objects.Shape import Shape
from Objects.Lane import Lane 
from Objects.Junction import Junction
from Objects.Relations import Relation
from Objects.Neighbor import Neighbor
from Objects.StopLane import StopLane 
from Objects.Overlap import Overlap
from Objects.Signal import Signal
from Objects.StopSign import StopSign
from Canvas import Canvas
from Pane import Pane
import Toolbars
import Save
from decimal import Decimal
import copy
import pickle


import qtmodern.styles
import qtmodern.windows
Image.MAX_IMAGE_PIXELS = 2991718400




   
class MapCreator(QMainWindow):

    SOLID_WHITE,DOTTED_WHITE,CRUB,SOLID_YELLOW,DOTTED_YELLOW = range(5)
    LANE,JUNCTION,RELATION,NEIGHBOR,NOTYPE,STOPLANE,OVERLAP,SIGNAL,STOPSIGN,DELNEIGHBOR,DELOVERLAP= range(11)
    def __init__(self):
        super(MapCreator, self).__init__()

        self.scaleFactor = 1.0
        self.fileSetings='./settings.pickle'
        if QFile.exists(self.fileSetings):
              with open(self.fileSetings, 'rb') as f:
                self.offsetX,self.offsetY,self.rotation = pickle.load(f)
        else: 
            self.offsetX,self.offsetY,self.rotation = 0,0,0

        self.createActions()
        self.createMenus()
        self.imageLabel=None
        self.setWindowTitle("MapCreator")
        self.resize(1280, 720)
        self.setToAllBt(False)
        self.Lanes=[]
        self.type=self.NOTYPE
        self.Junctions=[]
        self.Relations=[]
        self.Neighbors=[]
        self.StopLanes=[]
        self.Overlaps=[]
        self.StopSigns=[]
        self.Signals=[]
        self.file_save=""
        self.ruler.setEnabled(False)
        self.zoomInAct.setEnabled(True)
        self.zoomOutAct.setEnabled(True)

    def CreateToolbars(self):
	    Toolbars.CreateToolbars(self)

    def open(self):
       
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Geotiff File",
                QDir.currentPath(),"tif (*.tif*);;TIFF (*.TIF*)")
        if fileName:
            dsr = gdal.Open(fileName)
            np_array = np.array(dsr.ReadAsArray())
            if np_array.shape[0]==4:
                np_array=np_array[0]
            np_array_uint8 = (np_array).astype(np.uint8)

            self.geotiffScale=dsr.GetGeoTransform()[1]

            self.setToAllBt(True)
            width,height=dsr.RasterXSize,dsr.RasterYSize
            self.aspect=Decimal(float(height)/float(width))
            minabs=100
            if width>height:
                minh=3450
                for i in range(3450,3550,1):
                   if  abs(Decimal(i*self.aspect)-int(i*self.aspect))<minabs:
                       minabs=abs(Decimal(i*self.aspect)-int(i*self.aspect))
                       minh=i
                newHeight=minh
                newWidth=Decimal(newHeight*self.aspect)       
            else:
                minw=3450
                for i in range(3450,3550,1):
                   if  abs(Decimal(i*self.aspect)-int(i*self.aspect))<minabs:
                       minabs=abs(Decimal(i*self.aspect)-int(i*self.aspect))
                       minw=i
                newWidth=minw
                newHeight=Decimal(newWidth*self.aspect)
            self.resizeFactorWidth=Decimal(width/newWidth)
            self.resizeFactorHeight=Decimal(height/newHeight)  
            self.imageLabel =Canvas(np_array_uint8,newWidth,newHeight,self.resizeFactorWidth,self.resizeFactorHeight,self.geotiffScale)
            self.imageLabel.setScale(1)
            self.imageLabel.setMouseTracking(True)
            widget = QWidget(self)
            layout = QHBoxLayout(widget)
            self.leftScroll = Pane(
            Qt.AlignTop | Qt.AlignLeft, self)
            self.leftScroll.setWidgetResizable(True)
            self.scrollBars = {
            Qt.Vertical:  self.leftScroll.verticalScrollBar(),
            Qt.Horizontal: self.leftScroll.horizontalScrollBar()
           }
            self.leftScroll.addWidget(self.imageLabel)
            self.scaleFactor = 1.0
            layout.addWidget(self.leftScroll)

            self.setCentralWidget(widget)
            self.imageLabel.update()
            self.ruler.setEnabled(True)

          
            



    def leftChanged(self):
        self.imageLabel.currentLeft.type=self.ComboLaneBorderLeft.currentIndex()
        self.imageLabel.update()
    def rightChanged(self):
        self.imageLabel.currentRight.type=self.ComboLaneBorderRight.currentIndex()
        self.imageLabel.update() 
    def signToStopLane(self):
      self.imageLabel.signToStopLane(self.ComboLaneForStopSign.currentText())
    def zoomIn(self):
        if self.imageLabel is None:
            return
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)
    def wheelEvent(self,event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            try:
                if event.angleDelta().y()>0:
                    self.zoomIn()
                else:
                    self.zoomOut()
            except:
                pass


    def changeValueWidth(self):
        try:
            width=self.EditLaneWidth.text().replace(",",".")
            self.imageLabel.current.width=float(width)
        except:
            pass    
    def CreateErrorWindow(self,mainText,subText):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(mainText)
        msg.setWindowTitle(subText)
        msg.exec_()


    def getLastId(self,objlist):
        if len(objlist)==0:
            lenght=0
        else:
            lenght=int(objlist[-1].id.split("_")[1])+1
        return str(lenght)
    def createRoadFunc(self):
        self.type=self.LANE
        self.setToAllBt(False)
        self.acceptRoad.setEnabled(True)
        shape=Shape()
        shape.shape_type=shape.LANE
        last=self.getLastId(self.Lanes)
        shape.label="lane_"+last
        shapeLeft=Shape()
        shapeLeft.label="lane_"+last+"Left"
        shapeLeft.shape_type=shapeLeft.BORDER
        shapeRight=Shape()
        shapeRight.label="lane_"+last+"Right"
        shapeRight.shape_type=shapeRight.BORDER
        self.Lanes.append(Lane("lane_"+last,None,None,None,None))
        self.imageLabel.setDrawing(True)
        self.imageLabel.shapes[shape.label]=shape
        self.imageLabel.shapes[shapeLeft.label]=shapeLeft
        self.imageLabel.shapes[shapeRight.label]=shapeRight
        self.imageLabel.current=shape
        self.imageLabel.current.width=3 
        shapeLeft.type=self.ComboLaneBorderLeft.currentIndex()
        shapeRight.type=self.ComboLaneBorderRight.currentIndex()
        self.imageLabel.currentLeft=shapeLeft
        self.imageLabel.currentRight=shapeRight


        
        self.addToolBar(Qt.LeftToolBarArea,self.ToolbarLane)
        self.ToolbarLane.setVisible(True)  
    def acceptRoadFunc(self):
        if len(self.imageLabel.current.points)==0:
            self.CreateErrorWindow("Add points","")
            return
        if self.EditLaneWidth.text()=="" or self.EditLaneSpeed.text()=="":
            self.CreateErrorWindow("Fill all field","")
            return
        self.setToAllBt(False)

        self.createLeftRight.setEnabled(True)    
        self.removeToolBar(self.ToolbarLane)
        self.Lanes[-1].width=int(float(self.EditLaneWidth.text().replace(",",".")))
        self.Lanes[-1].speed=int(float(self.EditLaneSpeed.text().replace(",",".")))
        self.ToolbarLaneLeftRight.setVisible(True)
        self.addToolBar(Qt.LeftToolBarArea,self.ToolbarLaneLeftRight)
        self.imageLabel.current.shape_type=self.imageLabel.current.BORDER
  
        self.imageLabel.createBorder( self.Lanes[-1].width)       
    def createLeftRightFunc(self):
        self.type=self.NOTYPE
        self.setToAllBt(True)
        self.removeToolBar(self.ToolbarLaneLeftRight)
        self.Lanes[-1].idLeftBorder=self.ComboLaneBorderLeft.currentText()
        self.Lanes[-1].idRightBorder=self.ComboLaneBorderRight.currentText()
        self.imageLabel.currentRight=None
        self.imageLabel.currentLeft=None
        self.imageLabel.current=None
    def createjunctionFunc(self):
        self.type=self.JUNCTION
        self.setToAllBt(False)
        self.getBezier.setEnabled(True)
        self.acceptjunction.setEnabled(True)
        last=self.getLastId(self.Junctions)
        junction=Junction("junction_"+last)
        
        shape=Shape()
        shape.label="junction_"+last
        shape.shape_type=shape.JUNCTION
        self.Junctions.append(junction)
        self.imageLabel.shapes[shape.label]=shape
        self.imageLabel.setDrawing(True)
        self.imageLabel.current=shape

        self.addToolBar(Qt.LeftToolBarArea,self.ToolbarJunction)
        self.ToolbarJunction.setVisible(True)
    def acceptjunctionFunc(self):
        if len(self.imageLabel.current.points)<4:
            self.CreateErrorWindow("Curve is not created","")
            return
        self.type=self.NOTYPE
        self.setToAllBt(True)
        self.imageLabel.setDrawing(False)
        left,right=self.imageLabel.createBorder(self.Junctions[-1].width)
        for point in left:
            self.Junctions[-1].borderLeft.append([Decimal(point.x())*(self.resizeFactorWidth*Decimal(self.geotiffScale)),Decimal(point.y())*(self.resizeFactorHeight*Decimal(self.geotiffScale))])
        for point in right:
            self.Junctions[-1].borderRight.append([Decimal(point.x())*(self.resizeFactorWidth*Decimal(self.geotiffScale)),Decimal(point.y())*(self.resizeFactorHeight*Decimal(self.geotiffScale))])
        self.imageLabel.currentLeft=None
        self.imageLabel.currentRight=None
        self.imageLabel.current=None
        self.removeToolBar(self.ToolbarJunction)
        
        self.ToolbarJunction.setVisible(False)
    def getBezierFunc(self):
        if len(self.imageLabel.current.points)<3:
            self.CreateErrorWindow("Add three points","")
            return 
        bufPointmas=copy.deepcopy(self.imageLabel.current.points)
        pointmas=self.imageLabel.current.points

        bufArray=self.imageLabel.FindEdgeLanes(pointmas[0])

        pointmas.insert(0,bufArray[0])
        self.imageLabel.current.points[1]=bufArray[2]
        StartLane=self.imageLabel.shapes[bufArray[1]]
        bufArray1=self.imageLabel.FindEdgeLanes(pointmas[3])
        self.imageLabel.current.points[3]=bufArray1[2]

        FinishLane=self.imageLabel.shapes[bufArray1[1]]
        if pointmas[0]==-1 or pointmas[2]==-1:
            self.imageLabel.current.points=bufPointmas
            return

        pointmas=self.imageLabel.getBezierCurve(pointmas) 
        pointmas.pop(0)
        pointmas.append(bufArray1[0])
  
        self.imageLabel.current.points=pointmas
        self.imageLabel.shapes[self.imageLabel.current.label].points=pointmas
        lanest=[x for x in self.Lanes if x.id==bufArray[1]][0]
        lanefin=[x for x in self.Lanes if x.id==bufArray1[1]][0]
        self.Junctions[-1].speed=lanest.speed
        self.Junctions[-1].width=lanest.width
        relation=Relation(lanest.id,self.Junctions[-1].id)
        relation1=Relation(self.Junctions[-1].id,lanefin.id)
        self.Relations.append(relation)
        self.Relations.append(relation1)


    def findById(self,id, flist):
        for i in flist:
            if i.id == id:
                return i
        return None
    def loadFunc(self):# load objects from pickle file. 
        if self.imageLabel is None:
            self.open()
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Pickle file",
                QDir.currentPath(),"Plain text file (*.pickle)")
        with open(fileName, 'rb') as f:
            self.Junctions = pickle.load(f)
            for lane in self.Junctions:
                lane.points=[]
            self.Lanes = pickle.load(f)
            for lane in self.Lanes:
                lane.points=[]
                lane.leftBorderPoints=[]
                lane.rightBorderPoints=[]

            self.Relations = pickle.load(f)
            self.Neighbors=pickle.load(f)
            self.imageLabel.shapes = pickle.load(f)

            self.StopLanes=pickle.load(f)
            for lane in self.StopLanes:
                lane.points=[]
            self.Overlaps=pickle.load(f)
            for ovr in self.Overlaps:
                ovr.points=[]
            self.Signals=pickle.load(f)
            for signal in self.Signals:
                signal.points=[]
            self.StopSigns=pickle.load(f)
            for sign in self.StopSigns:
                sign.pointsStopLane=[]
            self.imageLabel.update()
            self.imageLabel.setScale(self.scaleFactor)


    def saveFunc(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Pickle file",
            QDir.currentPath(),"Plain text file (*.pickle)")
        Save.SaveTxt(self,fileName)
        pass
    
    def acceptNeighborFunc(self):
        if self.NeighborMainLanes.currentIndex()==0 or (self.ComboNeighborReverseLeft.currentIndex()==0 and self.ComboNeighborForwardLeft.currentIndex()==0 and self.ComboNeighborReverseRight.currentIndex()==0 and self.ComboNeighborForwardRight.currentIndex()==0):
            self.CreateErrorWindow("Add neighbor or main lane","")
            return
        self.type=self.NOTYPE
        self.setToAllBt(True)
        self.removeToolBar(self.ToolbarNeighbor)
        if self.ComboNeighborForwardLeft.currentIndex()!=0:
            ForwardLeft=self.ComboNeighborForwardLeft.currentText() 
        else:
           ForwardLeft=None 
        if self.ComboNeighborReverseLeft.currentIndex()!=0:
            ReverseLeft=self.ComboNeighborReverseLeft.currentText() 
        else:
           ReverseLeft=None 
        if self.ComboNeighborReverseRight.currentIndex()!=0:
            ReverseRight=self.ComboNeighborReverseRight.currentText() 
        else:
           ReverseRight=None 
        if self.ComboNeighborForwardRight.currentIndex()!=0:
            ForwardRight=self.ComboNeighborForwardRight.currentText() 
        else:
           ForwardRight=None 

        last=self.getLastId(self.Neighbors)
        neighbor=Neighbor("neighbor_"+last,self.NeighborMainLanes.currentText(),ForwardLeft,ReverseLeft,ForwardRight,ReverseRight)
        self.Neighbors.append(neighbor)
        self.NeighborMainLanes.clear() 
        self.ComboNeighborForwardLeft.clear() 
        self.ComboNeighborReverseLeft.clear() 
        self.ComboNeighborReverseRight.clear() 
        self.ComboNeighborForwardRight.clear() 
        print(self.Neighbors)

    def createNeighborFunc(self):
        self.type=self.NEIGHBOR
        self.setToAllBt(False)
        self.acceptNeighbor.setEnabled(True)
        self.NeighborMainLanes.clear()
        self.ComboNeighborForwardLeft.clear()
        self.ComboNeighborReverseLeft.clear()
        self.ComboNeighborForwardRight.clear()
        self.ComboNeighborReverseRight.clear()
        self.addObjsToComboBox(self.NeighborMainLanes,self.Lanes)
        self.addObjsToComboBox(self.ComboNeighborForwardLeft,self.Lanes)
        self.addObjsToComboBox(self.ComboNeighborReverseLeft,self.Lanes)
        self.addObjsToComboBox(self.ComboNeighborForwardRight,self.Lanes)
        self.addObjsToComboBox(self.ComboNeighborReverseRight,self.Lanes)
        self.addToolBar(Qt.LeftToolBarArea,self.ToolbarNeighbor)
        self.ToolbarNeighbor.setVisible(True)
        
    def addObjsToComboBox(self,combobox,listObj,isFirst=True):
        objs=[]
        if isFirst:
            objs.append(" ")
        for obj in listObj:
            objs.append(obj.id)
        combobox.addItems(objs)

    def cancelFunc(self):
        if self.type==self.NOTYPE:
            return
        self.setToAllBt(True)
       
        if self.type==self.LANE:
            del self.Lanes[-1]
            idLane=self.imageLabel.current.label
            del self.imageLabel.shapes[idLane]
            del self.imageLabel.shapes[idLane+"Left"]
            del self.imageLabel.shapes[idLane+"Right"]
            self.removeToolBar(self.ToolbarLane)
            self.removeToolBar(self.ToolbarLaneLeftRight)
        elif self.type==self.JUNCTION:
            del self.Junctions[-1]
            idLane=self.imageLabel.current.label
            del self.imageLabel.shapes[idLane]
            self.removeToolBar(self.ToolbarJunction)
        elif self.type==self.RELATION:
            del self.Relations[-1]
        elif self.type==self.NEIGHBOR:
            self.removeToolBar(self.ToolbarNeighbor)
        elif self.type==self.OVERLAP:
            self.removeToolBar(self.ToolbarOverlap)
            del self.Overlaps[-1]
        elif self.type==self.STOPLANE:
            self.removeToolBar(self.ToolbarStopLane)
            del self.imageLabel.shapes[self.StopLanes[-1].id]
            del self.StopLanes[-1]
        elif self.type==self.SIGNAL:
            del self.imageLabel.shapes[self.Signals[-1].id]
            del self.Signals[-1]
            self.removeToolBar(self.ToolbarSignal)
        elif self.type==self.STOPSIGN:
            idShape=self.StopSigns[-1].idStopLane
            if idShape is not None: 
                del self.imageLabel.shapes[idShape]
            del self.StopSigns[-1]
            self.removeToolBar(self.ToolbarStopSign)
        elif self.type==self.DELNEIGHBOR:
            self.removeToolBar(self.ToolbarDelNeighbor)
        elif self.type==self.DELOVERLAP:
            self.removeToolBar(self.ToolbarDelOverlap)
        self.type=self.NOTYPE
    def keyPressEvent(self, event):
    
        if event.key() == Qt.Key_Escape: # QtCore.Qt.Key_Escape is a value that equates to what the operating system passes to python from the keyboard when the escape key is pressed.
            self.cancelFunc()
    def createstopLaneFunc(self):   
        self.type=self.STOPLANE
        self.setToAllBt(False)
        self.acceptStopLane.setEnabled(True)
        self.addToolBar(Qt.LeftToolBarArea,self.ToolbarStopLane)
        self.ToolbarStopLane.setVisible(True)

        shape=Shape()
        last=self.getLastId(self.StopLanes)
        shape.label="stoplane_"+last
        shape.shape_type=shape.STOPLANE
        Stoplane=StopLane("stoplane_"+last)
        self.imageLabel.current=shape
        self.imageLabel.shapes[shape.label]=shape
        self.StopLanes.append(Stoplane)
    def acceptstopLaneFunc(self):
        if len(self.imageLabel.current.points)<2:
            self.CreateErrorWindow("Add points","")
            return
        self.type=self.NOTYPE
        self.setToAllBt(True)
        self.removeToolBar(self.ToolbarStopLane)

        self.imageLabel.current=None      
    def createOverlapFunc(self):
        self.setToAllBt(False)
        self.acceptOverlap.setEnabled(True)
        self.type=self.OVERLAP
        self.addToolBar(Qt.LeftToolBarArea,self.ToolbarOverlap)
        self.ToolbarOverlap.setVisible(True)

        self.addObjsToComboBox(self.ComboOverlapLanes,self.Lanes)
        self.addObjsToComboBox(self.ComboOverlapLanes,self.Junctions,isFirst=False)
        self.addObjsToComboBox(self.ComboOverlapSignal,self.Signals)
        self.addObjsToComboBox(self.ComboOverlapStopSign,self.StopSigns)


        shape=Shape()
        last=self.getLastId(self.Overlaps)
        shape.label="overlap_"+last
        self.imageLabel.current=shape
        self.imageLabel.shapes[shape.label]=shape
        shape.shape_type=shape.OVERLAP
        overlap=Overlap(shape.label)
        self.Overlaps.append(overlap)
    def acceptOverlapFunc(self):

        if self.ComboOverlapLanes.currentIndex()==0:
            self.CreateErrorWindow("Choose lane","")
            return
        if self.ComboOverlapSignal.currentIndex()==0 and self.ComboOverlapStopSign.currentIndex()==0:
            self.CreateErrorWindow("Choose stop sign or signal","")
            return
     
        if self.ComboOverlapSignal.currentIndex()!=0 and self.ComboOverlapStopSign.currentIndex()!=0:
            self.CreateErrorWindow("Choose only one object","")
            return

        for combobox in self.ComboboxesForOverlap:
            if combobox.currentIndex()!=0:
                self.Overlaps[-1].IdSecObject=combobox.currentText()
                idstopLane=None
                if combobox.currentText().find("stopsign")!=-1:
                    idstopLane=self.findById(self.Overlaps[-1].IdSecObject,self.StopSigns).idStopLane
                elif combobox.currentText().find("signal")!=-1:
                    idstopLane=self.findById(self.Overlaps[-1].IdSecObject,self.Signals).idStopLane
                else:
                    self.CreateErrorWindow("Select object","")
                    return
                if idstopLane is not None: 
                    point=self.imageLabel.intersectionLanes(self.imageLabel.shapes[idstopLane],self.imageLabel.shapes[self.ComboOverlapLanes.currentText()])
                    if  point is not None:
                        self.Overlaps[-1].pointOverlap=point
                        break
                    else:
                        self.CreateErrorWindow("no intersection with the lane","")
                        return

        print(self.Overlaps[-1].pointOverlap)
        self.type=self.NOTYPE
        self.Overlaps[-1].laneOverlapId=self.ComboOverlapLanes.currentText()   
        self.setToAllBt(True)
        self.type=self.NOTYPE
        self.removeToolBar(self.ToolbarOverlap)
        self.imageLabel.current=None
        self.ComboOverlapLanes.clear() 
        self.ComboOverlapSignal.clear() 
        self.ComboOverlapStopSign.clear() 
    def createSignalFunc(self):
        self.ComboSignalStopLanes.clear()
        self.setToAllBt(False)
        self.acceptSignal.setEnabled(True)
        self.addToolBar(Qt.LeftToolBarArea,self.ToolbarSignal)
        self.ToolbarSignal.setVisible(True)
        self.type=self.SIGNAL
        self.addObjsToComboBox(self.ComboSignalStopLanes,self.StopLanes)
        shape=Shape()
        last=self.getLastId(self.Signals)
        shape.label="signal_"+last
        shape.scale=self.scaleFactor
        shape.shape_type=shape.SIGNAL
        self.imageLabel.currentImage=shape
        signal=Signal(self.imageLabel.currentImage.label)
        self.Signals.append(signal)
        self.imageLabel.shapes[shape.label]=shape
       
    
    def acceptSignalFunc(self):
        if self.ComboSignalStopLanes.currentIndex()==0:
            self.CreateErrorWindow("Choose stoplane","")
            return
        if len(self.imageLabel.currentImage.points)==0:
            self.CreateErrorWindow("Choose signal place on map","")
            return

        self.type=self.NOTYPE
        self.setToAllBt(True)
        self.removeToolBar(self.ToolbarSignal) 
        self.Signals[-1].idStopLane=self.ComboSignalStopLanes.currentText()
        self.imageLabel.currentImage=None

        
    def createStopSignFunc(self):
        self.ComboLaneForStopSign.clear()
        self.type=self.STOPSIGN
        self.setToAllBt(False)
        self.acceptStopSign.setEnabled(True)
        self.addToolBar(Qt.LeftToolBarArea,self.ToolbarStopSign)
        self.ToolbarStopSign.setVisible(True)
        self.addObjsToComboBox(self.ComboLaneForStopSign,self.StopLanes)
        shape=Shape()
        last=self.getLastId(self.StopSigns)
        shape.label="stopsign_"+last
        shape.shape_type=shape.STOPSIGN
        self.imageLabel.currentImage=shape
        stopsign=StopSign(shape.label)
        self.StopSigns.append(stopsign)
        self.imageLabel.shapes[shape.label]=shape



    def acceptStopSignFunc(self):
        if self.ComboLaneForStopSign.currentIndex()==0:
            self.CreateErrorWindow("Choose stoplane","")
            return
        self.type=self.NOTYPE
        self.setToAllBt(True)
        self.removeToolBar(self.ToolbarStopSign)
        idStopLane=self.ComboLaneForStopSign.currentText()
        self.StopSigns[-1].idStopLane=idStopLane
        self.imageLabel.shapes[idStopLane].isStopSign=True
        
    def chooseObjectFunc(self):
        index=self.ComboObject.currentIndex()
        if index==1:
            self.createSignalFunc()
        elif index==2:
            self.createStopSignFunc()


    def rulerFunc(self):
        if self.imageLabel.Ruler== None:
            shape=Shape()
            shape.label="Ruler"
            shape.shape_type=shape.RULER
            self.imageLabel.Ruler=shape
            
        else:
            self.imageLabel.Ruler=None
            self.imageLabel.update()


    def offsetsFunc(self):
        x,y,r,res=OffsetsDialog.getOffsets( self.offsetX,self.offsetY,self.rotation)
        if not x:x=0
        if not y:y=0
        if not r:r=0
        if res:self.offsetX,self.offsetY,self.rotation=x,y,r


    def delNeighborFunc(self):
        self.labelLeftForward.setText(" ")
        self.labelLeftReverse.setText(" ")
        self.labelRightForward.setText(" ")
        self.labelRightReverse.setText(" ")
        self.setToAllBt(False)
        self.ComboneighborIdMainLane.clear() 
        self.finishNeighborDeletion.setEnabled(True)
        self.addToolBar(Qt.LeftToolBarArea,self.ToolbarDelNeighbor)
        self.ToolbarDelNeighbor.setVisible(True) 
        self.type=self.DELNEIGHBOR
        objs=[]
        objs.append(" ")
        for obj in self.Neighbors:
            objs.append(obj.id+"/"+obj.mainLane)
        self.ComboneighborIdMainLane.addItems(objs)


    def addLabelForNeighborDeletion(self):
        strCombo=self.ComboneighborIdMainLane.currentText()
        
        idNeighbor=strCombo.split("/")[0]

        Neighbor=self.findById(idNeighbor,self.Neighbors)
        if Neighbor is None:
            return
        if Neighbor.leftForward is not None:
            self.labelLeftForward.setText("Left forward id: " + Neighbor.leftForward)
        if Neighbor.leftReverse is not None:
            self.labelLeftReverse.setText("Left reverse id: " + Neighbor.leftReverse)
        if Neighbor.RightForward is not None:
            self.labelRightForward.setText("Right forward id: " + Neighbor.RightForward)
        if Neighbor.RightReverse is not None:
            self.labelRightReverse.setText("Right reverse id: " + Neighbor.RightReverse)




    def finishNeighborDeletionFunc(self):
        if self.ComboneighborIdMainLane.currentText()==" ":
            self.CreateErrorWindow("Choose neighbor", "")
            return
        self.setToAllBt(True)
        self.removeToolBar(self.ToolbarDelNeighbor)
        strCombo=self.ComboneighborIdMainLane.currentText()
        self.type=self.NOTYPE
        idNeighbor=strCombo.split("/")[0]
        Neighbor=self.findById(idNeighbor,self.Neighbors)
        self.Neighbors.remove(Neighbor)

    def delOverlapFunc(self):
        
        self.setToAllBt(False)
        self.ComboDelOverlap.clear() 
        self.finishOverlapDeletion.setEnabled(True)
        self.addToolBar(Qt.LeftToolBarArea,self.ToolbarDelOverlap)
        self.ToolbarDelOverlap.setVisible(True) 
        self.type=self.DELOVERLAP
        objs=[]
        objs.append(" ")
        for obj in self.Overlaps:
            objs.append(obj.id+"/"+obj.laneOverlapId+"/"+obj.IdSecObject)
        self.ComboDelOverlap.addItems(objs)

    
    def finishOverlapDeletionFunc(self):
        if self.ComboDelOverlap.currentText()==" ":
            self.CreateErrorWindow("Choose overlap", "")
            return
        self.setToAllBt(True)
        self.removeToolBar(self.ToolbarDelOverlap)
        strCombo=self.ComboDelOverlap.currentText()
        idOverlap=strCombo.split("/")[0]
        self.type=self.NOTYPE
        overlap=self.findById(idOverlap,self.Overlaps)
        self.Overlaps.remove(overlap)

    
    def createActions(self):
        self.openAct = QAction("&Open geotiff", self, shortcut="Ctrl+O",
                triggered=self.open)

        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                triggered=self.close)

        self.zoomInAct = QAction("Zoom &In (25%)", self, shortcut="Ctrl++",
                enabled=False, triggered=self.zoomIn)

        self.zoomOutAct = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+-",
                enabled=False, triggered=self.zoomOut)

        self.createRoad = QAction("&Road", self, enabled=True,
                checkable=False, triggered=self.createRoadFunc)
        self.acceptRoad = QAction("&Create", self, enabled=True,
                checkable=False,  triggered=self.acceptRoadFunc)
        self.createLeftRight = QAction("&Create", self, enabled=True,
                checkable=False,  triggered=self.createLeftRightFunc)
               
        self.save=QAction("&Save map", self, enabled=True,
                checkable=False,  triggered=self.saveFunc)   
       
        self.createjunction=QAction("&Junction", self, enabled=True,
                checkable=False,  triggered=self.createjunctionFunc)     
        self.acceptjunction=QAction("&Create", self, enabled=True,
                checkable=False,  triggered=self.acceptjunctionFunc)  
        self.getBezier=QAction("&Create Curve", self, enabled=True,
                checkable=False,  triggered=self.getBezierFunc)      
        self.load=QAction("&Load map", self, enabled=True,
                checkable=False,  triggered=self.loadFunc)         
        self.createNeighbor=QAction("&Neighbor", self, enabled=True,
                checkable=False,  triggered=self.createNeighborFunc) 
        self.acceptNeighbor=QAction("&Create", self, enabled=True,
                checkable=False,  triggered=self.acceptNeighborFunc) 

        self.cancel=QAction("&Cancel", self, enabled=True,
                checkable=False,  triggered=self.cancelFunc)
        self.createStopLane=QAction("&Stop Lane", self, enabled=True,
                checkable=False,  triggered=self.createstopLaneFunc)         
        self.acceptStopLane=QAction("&Create", self, enabled=True,
                checkable=False,  triggered=self.acceptstopLaneFunc)    

        self.createOverlap=QAction("&Overlap", self, enabled=True,
                checkable=False,  triggered=self.createOverlapFunc)         
        self.acceptOverlap=QAction("&Create", self, enabled=True,
                checkable=False,  triggered=self.acceptOverlapFunc)
        self.createSignal=QAction("&Signal", self, enabled=True,
                checkable=False,  triggered=self.createSignalFunc)
        self.acceptSignal=QAction("&Create", self, enabled=True,
                checkable=False,  triggered=self.acceptSignalFunc) 
        self.createStopSign=QAction("&Signal", self, enabled=True,
                checkable=False,  triggered=self.createStopSignFunc)
        self.acceptStopSign=QAction("&Create", self, enabled=True,
                checkable=False,  triggered=self.acceptStopSignFunc) 
        self.chooseObject=QAction("&Create object", self, enabled=True,
                checkable=False,  triggered=self.chooseObjectFunc)  

        self.ruler=QAction("&Ruler", self, enabled=True,
                checkable=True,  triggered=self.rulerFunc)  
        self.offsets=QAction("&Offsets setting", self, enabled=True,
                checkable=False,  triggered=self.offsetsFunc)  

        self.delNeighbor=QAction("&Del neighbor", self, enabled=True,
                checkable=False,  triggered=self.delNeighborFunc)  
        self.finishNeighborDeletion=QAction("&Delete", self, enabled=True,
                checkable=False,  triggered=self.finishNeighborDeletionFunc)

        self.delOverlap=QAction("&Del overlap", self, enabled=True,
                checkable=False,  triggered=self.delOverlapFunc)  
        self.finishOverlapDeletion=QAction("&Delete", self, enabled=True,
                checkable=False,  triggered=self.finishOverlapDeletionFunc)    
        
    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.load)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.save)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.offsets)
        self.fileMenu.addAction(self.exitAct)
        self.fileMenu.addSeparator()
        
        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)

        self.viewMenu.addSeparator()


        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)

        self.CreateToolbars()
        
    def setToAllBt(self,val):
        self.createRoad.setEnabled(val)
        self.acceptRoad.setEnabled(val)
        self.createLeftRight.setEnabled(val)
        self.createjunction.setEnabled(val)
        self.acceptjunction.setEnabled(val)
        self.save.setEnabled(val)
        self.getBezier.setEnabled(val)
        self.createNeighbor.setEnabled(val)
        self.acceptNeighbor.setEnabled(val)
        self.createOverlap.setEnabled(val)
        self.acceptOverlap.setEnabled(val)
        self.chooseObject.setEnabled(val)
        self.createStopLane.setEnabled(val)
        self.acceptStopLane.setEnabled(val)
        self.createSignal.setEnabled(val)
        self.acceptSignal.setEnabled(val)
        self.createStopSign.setEnabled(val)
        self.acceptStopSign.setEnabled(val)
        self.delNeighbor.setEnabled(val)
        self.delOverlap.setEnabled(val)



    def scaleImage(self, factor):
        self.scaleFactor *= factor
        
        self.leftScroll.removeWidget(self.imageLabel)
        self.leftScroll.addWidget(self.imageLabel)
        
        self.imageLabel.setScale(self.scaleFactor)
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.PixMap.size())
        self.zoomInAct.setEnabled(self.scaleFactor < 5)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.0005)

  

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    imageViewer =  qtmodern.windows.ModernWindow(MapCreator())
    imageViewer.setWindowIcon(QIcon('./static/icon.png'))
    imageViewer.show()


    sys.exit(app.exec_())


