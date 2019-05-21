#import cv2
import math
import numpy as np
from map import map_road_pb2
from map import map_lane_pb2
from map import map_pb2
from utils import distance
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Polygon, Point


class RoadObject(object):

    def __init__(self, id):
        self._id = id

    def get_id(self):
        return self._id

class Lane(RoadObject):

    def __init__(self, id, map):
        super(Lane, self).__init__(id)
        self.lane = map.lane.add()
        self.lane.id.id = str(id)

    def get_polygon(self):
        return self._polygon


    def set_length(self, points):
        length = 0
        for i in range(1, len(points)):
            length += distance(points[i - 1], points[i])
        self.lane.length = length
        return length

    def set_speed_limit(self, speed_limit):
        self.lane.speed_limit = speed_limit

    def add_overlap(self, id):
        self.lane.overlap_id.add().id = str(id)

    def add_predecessor(self, id):
        self.lane.predecessor_id.add().id = str(id)

    def add_successor(self, id):
        self.lane.successor_id.add().id = str(id)

    def add_left_neighbor_forward(self, id):
        self.lane.left_neighbor_forward_lane_id.add().id = str(id)

    def add_right_neighbor_forward(self, id):
        self.lane.right_neighbor_forward_lane_id.add().id = str(id)

    def add_left_neighbor_reverse(self, id):
        self.lane.left_neighbor_reverse_lane_id.add().id = str(id)

    def add_right_neighbor_reverse(self, id):
        self.lane.right_neighbor_reverse_lane_id.add().id = str(id)    

    def set_type(self, type):
        self.lane.type = type

    def set_turn(self, turn):
        self.lane.turn = turn

    def set_direction(self, direction):
        self.lane.direction = direction

    def set_left_lane_boundary_type(self, type, virtual):
        boundary_type = self.lane.left_boundary.boundary_type.add()
        boundary_type.types.append(type)
        self.lane.left_boundary.virtual = virtual 

    def set_right_lane_boundary_type(self, type, virtual):
        boundary_type = self.lane.right_boundary.boundary_type.add()
        boundary_type.types.append(type)
        self.lane.right_boundary.virtual = virtual 

    def add_left_lane_boundary(self, x, y, z, heading):  
        left_boundary = self.lane.left_boundary.curve.segment.add()
        left_boundary.heading = heading
        left_boundary.start_position.x = x
        left_boundary.start_position.y = y
        left_boundary.start_position.z = z
        left_boundary.s = 0
        return left_boundary

    def add_right_lane_boundary(self, x, y, z, heading): 
        right_boundary = self.lane.right_boundary.curve.segment.add()
        right_boundary.heading = heading
        right_boundary.start_position.x = x
        right_boundary.start_position.y = y
        right_boundary.start_position.z = z
        right_boundary.s = 0
        return right_boundary

    def add_central_curve(self, x, y, z, heading):  
        central_curve = self.lane.central_curve.segment.add()
        central_curve.heading = heading
        central_curve.start_position.x = x
        central_curve.start_position.y = y
        central_curve.start_position.z = z
        central_curve.s = 0
        return central_curve

   

    

    def lane_sampling(self, points, width, left_boundary, right_boundary, central_curve,left_points,right_points,thresh, do_sampling=False):
        length = len(points)
        lengthL = len(left_points)

        self.left_poly = []
        self.right_poly = []

        # variables used to compute central line and boundaries length
        c_dist = 0
        cx, cy = (central_curve.start_position.x, central_curve.start_position.y)
        l_dist = 0
        lx, ly = (left_boundary.start_position.x, central_curve.start_position.y)
        r_dist = 0
        rx, ry = (right_boundary.start_position.x, central_curve.start_position.y)
        left_lane_x = []
        right_lane_x = []
        left_lane_y = []
        right_lane_y = []

        for i in range(length):
            if i > 1:
                p = Point(points[i-1])
                p2 = Point(points[i])

            if i < length - 1:
                p = Point(points[i])
                p2 = Point(points[i + 1])
            else:
                p = Point(points[i - 1])
                p2 = Point(points[i])
            distance = width / 2.0

            central_point = central_curve.line_segment.point.add()
            if i < length - 1:
                central_point.x = p.x
                central_point.y = p.y
                central_point.z = points[i][2]
            else:
                central_point.x = p2.x
                central_point.y = p2.y
                central_point.z = points[i-1][2]
            c_dist += math.sqrt(math.pow(central_point.x - cx, 2) + math.pow(central_point.y - cy, 2))
            if i<len(left_points):
                lp,rp=left_points[i],right_points[i]
            else:
                continue
            if(i > 0 and abs(lp[0] - prevlx) < thresh and abs(lp[1] - prevly) < thresh):
                if(i > 0 and abs(rp[0] - prevrx) < thresh and abs(rp[1] - prevry) < thresh):
                    continue
                else:
                    right_bound_point = right_boundary.line_segment.point.add()
                    right_bound_point.x = rp[0]
                    right_bound_point.y = rp[1]
                    right_bound_point.z = points[i][2]
                    right_lane_x.append(rp[0])
                    right_lane_y.append(rp[1])


                    r_dist += math.sqrt(math.pow(rp[0] - rx, 2) + math.pow(rp[1] - ry, 2))
                    rx = rp[0]
                    ry = rp[1]
            else:
                if(i > 0 and abs(rp[0] - prevrx) < thresh and abs(rp[1] - prevry) < thresh):
                    continue
                else:
                    right_bound_point = right_boundary.line_segment.point.add()
                    right_bound_point.x = rp[0]
                    right_bound_point.y = rp[1]
                    right_bound_point.z = points[i][2]
                    right_lane_x.append(rp[0])
                    right_lane_y.append(rp[1])

                    r_dist += math.sqrt(math.pow(rp[0] - rx, 2) + math.pow(rp[1] - ry, 2))
                    rx = rp[0]
                    ry = rp[1]

                left_bound_point = left_boundary.line_segment.point.add()
                left_bound_point.x = lp[0]
                left_bound_point.y = lp[1]
                left_bound_point.z = points[i][2]
                left_lane_x.append(lp[0])
                left_lane_y.append(lp[1])

                l_dist += math.sqrt(math.pow(lp[0] - lx, 2) + math.pow(lp[1] - ly, 2))
                lx = lp[0]
                ly = lp[1]

            # plt.plot(rp[0], rp[1], 'ro')
            # plt.plot(lp[0], lp[1], 'bo')
            
            prevrx, prevry, prevlx, prevly = rp[0], rp[1], lp[0], lp[1]

            ####

            
           
            cx = central_point.x
            cy = central_point.y

            if i < length - 1:
                self.left_poly.append(np.array(lp))
                self.right_poly.append(np.array(rp))

            # Get distance from lane start
            if i > 0:
                line = LineString(points[:i + 1])
                dist = line.length
            else:
                dist = 0

            left_sample = self.lane.left_sample.add()
            left_sample.s = dist
            left_sample.width = width / 2.0

            right_sample = self.lane.right_sample.add()
            right_sample.s = dist
            right_sample.width = width / 2.0

        central_curve.length = c_dist
        left_boundary.length = l_dist
        right_boundary.length = r_dist
        
        self._polygon = np.array(self.left_poly + list(reversed(self.right_poly)))
        z = np.zeros(len(left_lane_x))
        left_bound_point = np.array(list(zip(left_lane_x, left_lane_y, z)))
        right_bound_point= np.array(list(zip(right_lane_x, right_lane_y, z)))
        return left_lane_x, right_lane_x, left_lane_y, right_lane_y,left_bound_point,right_bound_point 

    def justGetMeTheLanes(self, points, width, thresh):
        length = len(points)
        left_lane_x = []
        right_lane_x = []
        left_lane_y = []
        right_lane_y = []
        for i in range(length):
            if i > 1:
                p = Point(points[i-1])
                p2 = Point(points[i])
            if i < length - 1:
                p = Point(points[i])
                p2 = Point(points[i + 1])
            else:
                p = Point(points[i - 1])
                p2 = Point(points[i])
            distance = width / 2.0
            lp, rp = self.convert(p, p2, distance, use_first=(i != length - 1))

            if(i > 0 and abs(lp[0] - prevlx) < thresh and abs(lp[1] - prevly) < thresh):
                if(i > 0 and abs(rp[0] - prevrx) < thresh and abs(rp[1] - prevry) < thresh):
                    continue
                else:
                    right_lane_x.append(rp[0])
                    right_lane_y.append(rp[1])
            else:
                if(i > 0 and abs(rp[0] - prevrx) < thresh and abs(rp[1] - prevry) < thresh):
                    continue
                else:
                    right_lane_x.append(rp[0])
                    right_lane_y.append(rp[1])
                left_lane_x.append(lp[0])
                left_lane_y.append(lp[1])
            prevrx, prevry, prevlx, prevly = rp[0], rp[1], lp[0], lp[1]
        return left_lane_x, right_lane_x, left_lane_y, right_lane_y

    def convert(self, p, p2, distance, use_first=True):
        delta_y = p2.y - p.y
        delta_x = p2.x - p.x

        if use_first:
            point = p
        else:
            point = p2

        left_angle = math.atan2(delta_y, delta_x) + math.pi / 2.0
        right_angle = math.atan2(delta_y, delta_x) - math.pi / 2.0

        lp = []
        lp.append(point.x + (math.cos(left_angle) * distance))
        lp.append(point.y + (math.sin(left_angle) * distance))

        rp = []
        rp.append(point.x + (math.cos(right_angle) * distance))
        rp.append(point.y + (math.sin(right_angle) * distance))
        return lp, rp

    def add(self, points, speed_limit, lane_turn, lane_type, direction, width, left_points,right_points,thresh):
        self.set_length(points)
        self.set_speed_limit(speed_limit)
        self.set_turn(lane_turn)
        self.set_type(lane_type)
        self.set_direction(direction)

        path = LineString(points)
        p = path.interpolate(0)
        p2 = path.interpolate(0.5)
        distance = width / 2.0
        lp, rp = self.convert(p, p2, distance)

        central_curve = self.add_central_curve(points[0][0], points[0][1], points[0][2], 0)
        #left_boundary = self.add_left_lane_boundary(lp[0], lp[1], points[0][2], 0)
        #right_boundary = self.add_right_lane_boundary(rp[0], rp[1], points[0][2], 0)

        left_boundary = self.add_left_lane_boundary(left_points[0][0], left_points[0][1], 0, 0)
        right_boundary = self.add_right_lane_boundary(right_points[0][0], right_points[0][1], 0, 0)
        left_lane_x = []
        right_lane_x = []
        left_lane_y = []
        right_lane_y = []

        left_lane_x, right_lane_x, left_lane_y, right_lane_y,lb_points,rb_points = self.lane_sampling(points, width, left_boundary, right_boundary, central_curve,left_points,right_points,thresh,False)

        return left_lane_x, right_lane_x, left_lane_y, right_lane_y,lb_points,rb_points

class Road(RoadObject):

    def __init__(self, id, map):
        super(Road, self).__init__(id)
        self.road = map.road.add()
        self.road.id.id = str(id)

    def getID(self):
        return self._id

    def add_section(self, id):
        self.section = self.road.section.add()
        self.section.id.id = str(id)

    def add_lanes_to_section(self, lanes):
            self.section.lane_id.add().id = str(lanes)

    def add_junction(self, id):
        self.road.junction_id.id = str(id)

    def add_road_boundary(self, points, type, heading):
        edge = self.section.boundary.outer_polygon.edge.add()
        edge.type = type
        segment = edge.curve.segment.add()
        length = 0
        prevX, prevY,_ = points[0]
        for point in points[0:]:
            p = segment.line_segment.point.add()
            p.x, p.y,_ = point
            length += math.sqrt(math.pow(p.x - prevX, 2) + math.pow(p.y - prevY, 2))
            prevX = p.x
            prevY = p.y


    def add(self, lane, section_id, junction_ids, lane_ids, heading):
        self.add_section(section_id)
        for j in junction_ids:
            self.add_junction(j)
        self.add_lanes_to_section(lane_ids)
        lx = lane.left_poly[0][0]
        ly = lane.left_poly[0][1]
        self.add_road_boundary(lane.left_poly, map_road_pb2.BoundaryEdge.LEFT_BOUNDARY, heading)
        rx = lane.right_poly[0][0]
        ry = lane.right_poly[0][1]
        self.add_road_boundary(lane.right_poly, map_road_pb2.BoundaryEdge.RIGHT_BOUNDARY, heading)

class Signal(RoadObject):
    def __init__(self,id,map):
        super(Signal,self).__init__(id)
        self.signal=map.signal.add()
        self.signal.id.id=id
        self.signal.type=5
        self._id=id
    def get_polygon(self):
        return self.signal.boundary

    def get_id(self):
        return self._id

    def addBoundary(self,pointLight,pointsStoLane):
        boundary=self.signal.boundary.point.add()
        boundary.x=pointLight[0]
        boundary.y=pointLight[1]
        boundary=self.signal.boundary.point.add()
        boundary.x=pointLight[0]
        boundary.y=pointsStoLane[1][1]
        boundary=self.signal.boundary.point.add()
        boundary.x=pointsStoLane[1][0]
        boundary.y=pointsStoLane[1][1]
        boundary=self.signal.boundary.point.add()
        boundary.x=pointsStoLane[0][0]
        boundary.y=pointsStoLane[0][1]

       
    def addsubsignal(self,point):
        subsignal=self.signal.subsignal.add()
        subsignal.id.id="0"
        subsignal.type=2
        subsignal.location.x=point[0]
        subsignal.location.y=point[1]*-1
        subsignal.location.z=8.11499977
        subsignal=self.signal.subsignal.add()
        subsignal.id.id="1"
        subsignal.type=2
        subsignal.location.x=point[0]
        subsignal.location.y=point[1]*-1
        subsignal.location.z=7.292500
        subsignal=self.signal.subsignal.add()
        subsignal.location.x=point[0]
        subsignal.location.y=point[1]*-1
        subsignal.location.z=6.47
        subsignal.id.id="2"
        subsignal.type=2

    
    def add_overlap(self, id):
        self.signal.overlap_id.add().id = str(id)
    def addStopLine(self,points):
        stop_lane=self.signal.stop_line.add()
        line_segment=stop_lane.segment.add()
		
        for point in points:
            curvePoint=line_segment.line_segment.point.add()
            curvePoint.x=point[0]
            curvePoint.y=point[1]
            curvePoint.z=0
        
class Overlap(RoadObject):

    def __init__(self, id, map):
        super(Overlap, self).__init__(id)
        self.overlap = map.overlap.add()
        self.overlap.id.id = id
        self._id=id


    def get_id(self):
        return self._id


    def _complete_info(self, info, dist):
        info.start_s = dist
        info.end_s = dist+1.699
        info.is_merge = False

    def addLane(self, idLane,dist):
        object1 = self.overlap.object.add()
        object1.id.id = idLane
        object1.lane_overlap_info.SetInParent()
        self._complete_info(object1.lane_overlap_info, dist)
    def addStopLine(self,idStopLane):
        stopLaneOverlap=self.overlap.object.add()
        stopLaneOverlap.id.id=idStopLane
        stopLaneOverlap.stop_sign_overlap_info.SetInParent()




    def addSignal(self,signal):
        signalOverlap = self.overlap.object.add()
        signalOverlap.id.id = signal
       
        signalOverlap.signal_overlap_info.SetInParent()
           
class Junction(RoadObject):

    def __init__(self, id, map):
        super(Junction, self).__init__(id)
        self.junction = map.junction.add()
        self.junction.id.id = id

    def get_id(self):
        return self._id

    def get_polygon(self):
        return self._polygon

    def add_overlap(self, id):
        self.junction.overlap_id.add().id = str(id)

    def add(self, junc_poly):
        self._polygon = np.array(junc_poly)

        for vertex in junc_poly:
            point = self.junction.polygon.point.add()
            point.x, point.y = vertex

class StopLane(RoadObject):
    def __init__(self, id, map):
        self.stop_sign = map.stop_sign.add()
        self.stop_lane=self.stop_sign.stop_line.add()
        self.stop_sign.id.id = id 
        self.stop_sign.type=2
        self._id=id

    def add_overlap(self, id):
        self.stop_sign.overlap_id.add().id = str(id)
    def add_central_curve(self, points): 

        central_curve = self.stop_lane.segment.add()
        central_curve.heading = 1
        central_curve.start_position.x = float(points[0][0])
        central_curve.start_position.y = float(points[0][1])
        central_curve.start_position.z = 0
        central_curve.s = 0

        for point in points:
            curvePoint=central_curve.line_segment.point.add()
            curvePoint.x= float(point[0])
            curvePoint.y= float(point[1])
            curvePoint.z=0
            

        return central_curve