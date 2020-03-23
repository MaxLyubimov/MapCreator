#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np
from Lib import distance 

import math
DEFAULT_LINE_COLOR_LEFT = QColor(0, 0, 220, 128)
DEFAULT_LINE_COLOR_RIGHT = QColor(20, 200, 20, 128)
DEFAULT_LINE_COLOR = QColor(220, 0, 0, 128)
DEFAULT_PREVIEW_COLOR = QColor(123, 0, 200, 50)
DEFAULT_TRAJECTORY_COLOR = QColor(223, 233, 0, 250)
DEFAULT_STOPLINE_COLOR = QColor(220, 220, 0, 128)
DEFAULT_FILL_COLOR = QColor(255, 0, 0, 10)
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)
DEFAULT_SELECT_FILL_COLOR = QColor(0, 128, 255, 155)
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255,255, 255)
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 0, 0)


class Shape(object):
    P_SQUARE, P_ROUND = range(2)
    LANE,BORDER,JUNCTION,STOPLANE,OVERLAP,SIGNAL,STOPSIGN,RULER,PREVIEW,TRAJECTORY = range(10)
    MOVE_VERTEX, NEAR_VERTEX = range(2)
    SOLID_WHITE,DOTTED_WHITE,CRUB,SOLID_YELLOW,DOTTED_YELLOW=range(5)
    line_color = DEFAULT_LINE_COLOR
    lineLeft_color=DEFAULT_LINE_COLOR_LEFT
    lineRight_color=DEFAULT_LINE_COLOR_RIGHT
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 6
    scale = 1.0
    label_font_size = 14

    def __init__(self, label=None, shape_type=0, line_color=None,Angle="",index=None):

        self.label = label
        self.points = []
        self.Angle=Angle
        self.fill = False
        self.selected = False
        self.Index=index
        self.LaneChange=False
        self.turn=1
        self.type=self.SOLID_WHITE
        self.width=-1
        self.isStopSign=False
        self.shape_type = self.LANE
        self.max_piont_num = 4
        if shape_type == 1:
            self.shape_type = self.BORDER
            self.max_piont_num = 100
        self._highlightIndex = None
        self._highlightMode = self.NEAR_VERTEX
        self._highlightSettings = {
            self.NEAR_VERTEX: (1.5, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }

        self._closed = False

        if line_color is not None:
            self.line_color = line_color

    def set_shape_type(self, type):
        self.shape_type = type

    def get_shape_type(self):
        return self.shape_type

    def close(self):
        assert len(self.points) > 1
        self._closed = True


    def isLane(self):
        return self.shape_type == self.LANE

    def reachMaxPoints(self):
        if len(self.points) >= self.max_piont_num:
            return True
        return False
    
    def addPoint(self, point):
      
            self.points.append(point)

    def popPoint(self):
        if self.points:
            return self.points.pop()
        return None

    def isClosed(self):
        return self._closed

    def setOpen(self):
        self._closed = False

    def paint(self, painter,image=None,distance=None):

        if image!=None:
            painter.drawImage(self.points[0].x(), self.points[0].y(), image)
            if not self.isStopSign:
                return
        
        color = self.select_line_color if self.selected else self.line_color
        if self.shape_type==self.PREVIEW:
           color=DEFAULT_PREVIEW_COLOR
        if self.shape_type==self.TRAJECTORY:
            color=DEFAULT_TRAJECTORY_COLOR
        if self.shape_type==self.STOPLANE:
            color=DEFAULT_STOPLINE_COLOR
        if self.label.find("Left")!=-1:
            color=self.lineLeft_color
        elif self.label.find("Right")!=-1:
            color=self.lineRight_color  
        pen = QPen(color)
        if self.type==self.DOTTED_WHITE or self.type==self.DOTTED_YELLOW:
            pen.setStyle(Qt.CustomDashLine)
            pen.setDashPattern([5, 5, 5, 5])

        # Try using integer sizes for smoother drawing(?)

        pen.setWidth(max(1, int(round(3.0 / self.scale))))
        if self.shape_type==self.TRAJECTORY:
            pen.setWidth(max(1, int(round(1.0 / self.scale))))
        painter.setPen(pen)

        line_path = QPainterPath()
        vrtx_path = QPainterPath()

        line_path.moveTo(self.points[0])
        if self.isStopSign:
           painter.drawImage(self.points[0].x(), self.points[0].y(), image) 
        if self.shape_type!=self.PREVIEW:
            self.drawVertex(vrtx_path, 0)
        
        for i, p in enumerate(self.points): 
            if self.shape_type!=self.PREVIEW: 
                self.drawVertex(vrtx_path, i)
        
        painter.drawPath(line_path)
        if self.shape_type!=self.TRAJECTORY:
            painter.drawPath(vrtx_path)
            painter.fillPath(vrtx_path, self.vertex_fill_color)
        fontScale=12/self.scale
        if fontScale<2:fontScale=2
        if self.label is not None:
            for i in range(0,len(self.points)-1):
                painter.drawLine(self.points[i], self.points[i+1])
        if self.shape_type==self.RULER:
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont('Decorative', fontScale)) 
            painter.drawText(self.points[0], distance)
        elif self.label.find("Left")==-1 and self.label.find("Right")==-1:
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont('Decorative', fontScale))
            painter.drawText(self.points[int(len(self.points)/2)], self.label)
        
    def distance_between(self,p1,p2):
        return math.sqrt(math.pow(p2.x()-p1.x(),2)+math.pow(p2.y()-p1.y(),2))
   

    def drawVertex(self, path, i):
        d = self.point_size / self.scale
        if self.shape_type==self.TRAJECTORY:
            d=3/self.scale
        shape = self.point_type
        point = self.points[i]

        if i == self._highlightIndex:
            size, shape = self._highlightSettings[self._highlightMode]
            d *= size
        if self._highlightIndex is not None:
            self.vertex_fill_color = self.hvertex_fill_color
        else:
            self.vertex_fill_color = Shape.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            assert False, "unsupported vertex shape"

    def nearestVertex(self, point, epsilon):
        for i, p in enumerate(self.points):
            if distance(p - point) <= epsilon:
                return i
        return None

    def containsPoint(self, point):
        return self.makePath().contains(point)

    def makePath(self):
        path = QPainterPath(self.points[0])
        for p in self.points[1:]:
            path.lineTo(p)
        return path

    def boundingRect(self):
        return self.makePath().boundingRect()

    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]

    def moveVertexBy(self, i, offset):
        self.points[i] = self.points[i] + offset

    def highlightVertex(self, i, action):
        self._highlightIndex = i
        self._highlightMode = action

    def highlightClear(self):
        self._highlightIndex = None

  

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value
