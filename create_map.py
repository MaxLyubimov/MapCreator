import requests

import json

import matplotlib.pyplot as plt
import numpy as np
import utm
from map_elements import *
import math
from decimal import Decimal
import numpy as np
from map import map_road_pb2
from map import map_pb2
from map import map_lane_pb2
from map import map_crosswalk_pb2
from map import map_signal_pb2
from map import map_overlap_pb2
from map import map_stop_sign_pb2
from utils import distance
from shapely.geometry import LineString, Polygon, Point
import sys, json, numpy as np

from datetime import datetime

SOLID_YELLOW = map_lane_pb2.LaneBoundaryType.SOLID_YELLOW
CURB = map_lane_pb2.LaneBoundaryType.CURB
DOTTED_WHITE = map_lane_pb2.LaneBoundaryType.DOTTED_WHITE
UNKNOWN = map_lane_pb2.LaneBoundaryType.DOTTED_WHITE
DOTTED_YELLOW=map_lane_pb2.LaneBoundaryType.DOTTED_YELLOW
SOLID_WHITE=map_lane_pb2.LaneBoundaryType.SOLID_WHITE

class BaseMapGeneration():
	def addNeighbors (self,neighbors,lane):
		for elem in neighbors:
			if (elem.mainLane==lane.get_id()):
				if elem.leftForward is not None:
					lane.add_left_neighbor_forward(elem.leftForward)
				elif elem.leftReverse is not None:
					lane.add_left_neighbor_reverse(elem.leftReverse)	
				elif elem.RightForward is not None :
					lane.add_right_neighbor_forward(elem.RightForward)
				elif elem.RightReverse is not None:
					lane.add_right_neighbor_reverse(elem.RightReverse)	
	def addOverlaps (self,overlaps,obj):
		for elem in overlaps:
			if (elem.laneOverlapId==obj.get_id()):
				obj.add_overlap(elem.id)
			if (elem.IdSecObject==obj.get_id()):
				obj.add_overlap(elem.id)	
	def addRelations (self,relations,lane):

		for elem in relations:
			if (elem.successor==lane.get_id()):
				lane.add_successor(elem.predecessor)
			if (elem.predecessor==lane.get_id()):
				lane.add_predecessor(elem.successor)	
	def getBorderId(self,border):
		if (border=="SOLID_YELLOW"):
			return SOLID_YELLOW
		elif (border=="CURB"):
			return CURB
		elif (border=="DOTTED_WHITE"):
			return DOTTED_WHITE	
		elif (border=="DOTTED_YELLOW"):
			return DOTTED_YELLOW
		return SOLID_WHITE	
	def createRoad(self,map,roadid):
		road=Road(roadid,map)
		road.add_section("2")
		
		return road
	def make_lanes(self,points, map, id1,  border,direction,speed,borderleft,borderright,neighbors,width,leftborderPoint,rightBorderPoints,turn,road):
		lane = Lane(id1, map)
		main_lane_x=[]
		main_lane_y=[]
		left_lane_x=[]
		left_lane_y=[]
		right_lane_x=[]
		right_lane_y=[]
		if leftborderPoint!=None:
			for i in range(len(points)):
				if points[i]!=None:
					main_lane_x.append(float(points[i][0]))
					main_lane_y.append(float(points[i][1]))
			for i in range(len(leftborderPoint)):
					left_lane_x.append(float(leftborderPoint[i][0]))
					left_lane_y.append(float(leftborderPoint[i][1]))
			for i in range(len(rightBorderPoints)):
					right_lane_x.append(float(rightBorderPoints[i][0]))
					right_lane_y.append(float(rightBorderPoints[i][1]))
		
		z = np.zeros(len(main_lane_x))
		left_points = []
		mainPoints = np.array(list(zip(main_lane_x, main_lane_y, z)))

		leftPoints=np.array(list(zip(left_lane_x, left_lane_y, z)))
		rightsPoints=np.array(list(zip(right_lane_x, right_lane_y, z)))

		if (direction=='FORWARD'):
			direction=map_lane_pb2.Lane.FORWARD
		elif (direction=='BACKWARD'):
			direction=map_lane_pb2.Lane.BACKWARD	
		else:
			direction=map_lane_pb2.Lane.BIDIRECTION
		lane.add(mainPoints, speed, turn, map_lane_pb2.Lane.CITY_DRIVING,direction,width,leftborderPoint,rightBorderPoints,0.1)
		road.add_road_boundary(leftPoints,map_road_pb2.BoundaryEdge.LEFT_BOUNDARY,1)
		road.add_road_boundary(rightsPoints,map_road_pb2.BoundaryEdge.RIGHT_BOUNDARY,1)

		borderleft=self.getBorderId(borderleft)
		borderright=self.getBorderId(borderright)
		if(border == True):
			lane.set_left_lane_boundary_type(borderleft, False)
			lane.set_right_lane_boundary_type(borderright, False)
		else:
			lane.set_left_lane_boundary_type(UNKNOWN, True)
			lane.set_right_lane_boundary_type(UNKNOWN, True)
		return lane

		return [i for i in cls.__dict__.keys() if i[:1] != '_']
	def rotate(self,x,y,xo,yo,theta): 
		xr=math.cos(theta)*(x-xo)-math.sin(theta)*(y-yo)   + xo
		yr=math.sin(theta)*(x-xo)+math.cos(theta)*(y-yo)  + yo
		return [xr,yr]
	def make_arr(self,arr1, arr2):
		for i in range(len(arr1)):
			if type(arr1[i]) is list:
				arr2.append([float(arr1[i][0]), -1*float(arr1[i][1])])

	def start(self,roads,junctions,relations,neighbors,overlaps,signals,stopsigns,offsetx,offsety,rotation):
		map = map_pb2.Map()
		counter=0
		rotateangle=float(rotation)
		x=float(offsetx)
		y=float(offsety)
		for record in overlaps:
			overlap=Overlap(record.id,map)
			if record.IdSecObject.find("stopsign")!=-1:		
				overlap.addStopLine(record.IdSecObject)
			if record.IdSecObject.find("signal")!=-1:
				overlap.addSignal(record.IdSecObject)
			overlap.addLane(record.laneOverlapId,record.pointOverlap)
		for lanes in roads:
			counter+=1
			road=self.createRoad(map,"road_"+str(counter))
			if (lanes.Neighbors!=None):
				lanesxy = []
				self.make_arr(lanes.points,lanesxy)
				lanesxy_left = []
				self.make_arr(lanes.leftBorderPoints,lanesxy_left)
				lanesxy_right = []
				self.make_arr(lanes.rightBorderPoints,lanesxy_right)
				for i in range(len(lanesxy)):
					lanesxy[i]=self.rotate(lanesxy[i][0],lanesxy[i][1],0,0,math.radians(rotateangle) )
					lanesxy[i][1]+=y
					lanesxy[i][0]+=x
				for i in range(len(lanesxy_left)):
					lanesxy_left[i]=self.rotate(lanesxy_left[i][0],lanesxy_left[i][1],0,0,math.radians(rotateangle) )
					lanesxy_left[i][1]+=y
					lanesxy_left[i][0]+=x
				for i in range(len(lanesxy_right)):
					lanesxy_right[i]=self.rotate(lanesxy_right[i][0],lanesxy_right[i][1],0,0,math.radians(rotateangle) )
					lanesxy_right[i][1]+=y
					lanesxy_right[i][0]+=x
				l = self.make_lanes(lanesxy, map, lanes.id, True,lanes.direction,int(lanes.speed),lanes.idLeftBorder,lanes.idRightBorder,lanes.Neighbors,float(lanes.width),lanesxy_left,lanesxy_right,lanes.turn,road)
				self.addRelations(relations,l)
				self.addNeighbors(neighbors,l)
				self.addOverlaps(overlaps,l)
				road.add_lanes_to_section(lanes.id)			

		for junction in junctions:
			if junction.id is None:
				continue
			if junction.points is None:
				continue
			print(junction.id)
			print(junction.points)
			lanesxy = []
			counter+=1
			road=self.createRoad(map,"road_"+str(counter))
			self.make_arr(junction.points,lanesxy)
			for i in range(len(lanesxy)):
				lanesxy[i]=self.rotate(lanesxy[i][0],lanesxy[i][1],0,0,math.radians(rotateangle) )
				lanesxy[i][1]+=y
				lanesxy[i][0]+=x
			lanesxy_left = []
			self.make_arr(junction.borderLeft,lanesxy_left)
			for i in range(len(lanesxy_left)):
				lanesxy_left[i]=self.rotate(lanesxy_left[i][0],lanesxy_left[i][1],0,0,math.radians(rotateangle) )
				lanesxy_left[i][1]+=y
				lanesxy_left[i][0]+=x
			lanesxy_right = []
			self.make_arr(junction.borderRight,lanesxy_right)
			for i in range(len(lanesxy_right)):
				lanesxy_right[i]=self.rotate(lanesxy_right[i][0],lanesxy_right[i][1],0,0,math.radians(rotateangle) )
				lanesxy_right[i][1]+=y
				lanesxy_right[i][0]+=x
	

			l = self.make_lanes(lanesxy, map, junction.id, False,junction.direction,int(junction.speed),None,None,None,float(junction.width),lanesxy_left,lanesxy_right,junction.turn,road)
			road.add_lanes_to_section(junction.id)
		
			self.addOverlaps(overlaps,l)
			self.addRelations(relations,l)
		for stopsign in stopsigns: 
			st=StopLane(stopsign.id,map)
			points=[]
			self.make_arr(stopsign.pointsStopLane,points)
			for i in range(len(points)):
				points[i]=self.rotate(points[i][0],points[i][1],0,0,math.radians(rotateangle) )
				points[i][1]+=y
				points[i][0]+=x
			st.add_central_curve(points)
			self.addOverlaps(overlaps,st)
		for signal in signals: 
			st=Signal(signal.id,map)
			points=[]
			self.make_arr(signal.pointsStopLane,points)
			for i in range(len(points)):
				points[i]=self.rotate(points[i][0],points[i][1],0,0,math.radians(rotateangle) )
				points[i][1]+=y
				points[i][0]+=x
			signal.point=self.rotate(signal.point[0],signal.point[1],0,0,math.radians(-rotateangle) )
			signal.point[1]+=y
			signal.point[0]+=x
			signal.point=[float(signal.point[0]),float(signal.point[1])]
			st.addsubsignal(signal.point)
			st.addStopLine(points)
			self.addOverlaps(overlaps,st)
		map_file = open('base_map.txt', 'w')
		map_file.write(str(map))
		map_file.close()
