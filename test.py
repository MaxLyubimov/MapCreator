
import math


def cosdir(azim):
   az = math.radians(azim)
   cosa = math.sin(az)
   cosb = math.cos(az)
   return cosa,cosb

# original point
point = QgsPoint(147352.43, 94305.21)
for elem in layer.getFeatures():  
line = elem.geometry().asPolyline()
for seg_start, seg_end in pair(line):
    line_start = QgsPoint(seg_start)
    line_end = QgsPoint(seg_end) 
    length = math.sqrt(line_start.sqrDist(line_end))
    # direction cosines from the azimuth
    cosa, cosb = cosdir(line_start.azimuth(line_end))  
    # generate the points  in the same direction    
    resulting_point = QgsPoint(point.x()+(length*cosa), point.y()+(length*cosb))
    result= QgsGeometry.fromPolyline([point,resulting_point])
    point = resulting_point