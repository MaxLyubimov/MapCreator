import cv2
import math
import numpy as np
import pandas as pd
from shapely.geometry import Polygon


WHITE = [255, 255, 255]
BLACK = [0, 0, 0]

# Reduce number of points on contours such that Rviz can render them
FILTER_FACTOR = 2

# Vector map files
POINTS_COLUMNS = ["i", "j", "PID", "lat", "long"]

# init information
Density = 0.1643    # meters per pixel
# MAP_OFFSET = np.array([-16.43022, -16.43022, 0.000])  # for Town1
MAP_OFFSET = np.array([-21.87022, 91.04978])    # for Town2
LAT_LONG_COORD_TOP_LEFT = np.array([45., 45.])

MAX_LANE_PIXEL_WIDTH = 40
LANE_WIDTH = 3.98   # meters

# Compute distance between two points
def distance(point1, point2):
    return np.linalg.norm(point1 - point2)

# Display contours
def display_contours(contours, map_shape, window_name="Contours"):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    print(len(contours))
    if len(contours) != 0:
        white_img = np.zeros(map_shape)
        white_img[:] = WHITE
        # draw in red the contours that were found
        # cv2.drawContours(white_img, contours, -1, (0, 0, 255), 1)
        for line in contours:
            for i in range(len(line) - 1):
                cv2.line(white_img, tuple(line[i]), tuple(line[i + 1]), (0, 0, 255))
        cv2.imshow(window_name, white_img)
        cv2.imwrite('contours.png', white_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

# Points related functions
def transform_coord_to_lat_long(coord):
    R = 6378100  # Earth radius in meters
    lat = LAT_LONG_COORD_TOP_LEFT[0] + coord[0] / R
    long = LAT_LONG_COORD_TOP_LEFT[1] - coord[1] / R
    return np.array([lat, long])


def pixel_to_coord(point):
    i = point[0]
    j = point[1]
    relative_loc = Density * np.array([i, j])
    coord = relative_loc + MAP_OFFSET
    return coord

def get_pid(df_points, i, j):
    v = df_points[(df_points.i == i) & (df_points.j == j)]
    r = 0
    if len(v) > 0:
        r = v.PID.values[0]
    return r


def neighbours(point1, point2):
    if abs(point1[0] - point2[0]) <= 2 * FILTER_FACTOR and abs(point1[1] - point2[1]) <= 2 * FILTER_FACTOR:
        return True
    return False


def roadedge_point(road_edges, x, y):
    dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for i in range(FILTER_FACTOR):
        for j in range(FILTER_FACTOR):
            for dir in dirs:
                nx = x + i * dir[0]
                ny = y + j * dir[1]
                if get_pid(road_edges, nx, ny) != 0:
                    return 1
    return 0


# Lines related functions
def white_neighbor(map_img, x, y):
    neigh = [(-FILTER_FACTOR, 0), (0, -FILTER_FACTOR), (0, FILTER_FACTOR), (FILTER_FACTOR, 0)]

    for i in range(len(neigh)):
        nx = x + neigh[i][0]
        ny = y + neigh[i][1]
        if np.all(map_img[ny, nx] == WHITE):
            return 1
    return 0


def trim_contour(contours, data, handler):
    def get_contour_set(contour_set, x):
        # Determine what set of contours the contour belongs to
        px = x
        while px != contour_set[px]['set']:
            px = contour_set[px]['set']
        while x != px:
            aux = contour_set[x]['set']
            contour_set[x]['set'] = px
            x = aux

        return px

    def join_contours(contour_set, x, y):
        px = get_contour_set(contour_set, x)
        py = get_contour_set(contour_set, y)

        if contour_set[px]['size'] < contour_set[py]['size']:
            contour_set[px]['set'] = py
        else:
            contour_set[py]['set'] = px
            if contour_set[px]['size'] == contour_set[py]['size']:
                contour_set[px]['size'] += 1

    for i in range(len(contours)):
        delete_mask = []
        for j in range(len(contours[i])):
            x = contours[i][j][0]
            y = contours[i][j][1]
            if handler(data, x, y) != 0:
                delete_mask.append(j)
        contours[i] = np.delete(contours[i], delete_mask, axis=0)

    # Remove empty contours
    for i in range(len(contours)-1, -1, -1):
        if len(contours[i]) == 0:
            del contours[i]

    # Separate contours in components, if they were split
    new_contours = []
    for contour in contours:
        new_contour = [contour[0]]
        for i in range(1, len(contour)):
            if not neighbours(contour[i-1], contour[i]):
                new_contours.append(new_contour)
                new_contour = [contour[i]]
            else:
                new_contour.append(contour[i])

        new_contours.append(new_contour)

    # Group neighbouring contours
    contour_set = []
    for i in range(len(new_contours)):
        elem = {}
        elem = {}
        elem['set'] = i
        elem['size'] = 1
        contour_set.append(elem)
    for i in range(len(new_contours) - 1):
        for j in range(i + 1, len(new_contours)):
            if neighbours(new_contours[i][0], new_contours[j][0]) or \
               neighbours(new_contours[i][0], new_contours[j][-1]) or \
               neighbours(new_contours[i][-1], new_contours[j][0]) or \
               neighbours(new_contours[i][-1], new_contours[j][-1]):
                join_contours(contour_set, i, j)

    sets = {}
    for i in range(len(new_contours)):
        if contour_set[i]['set'] not in sets:
            sets[contour_set[i]['set']] = [new_contours[i]]
        else:
            sets[contour_set[i]['set']].append(new_contours[i])

    # Merge neighbouring contours
    final_contours = []
    for key in sets:
        set = sets[key]
        new_contour = set[0]
        del set[0]
        while len(set) > 0:
            for i in range(len(set)):
                if neighbours(new_contour[0], set[i][0]):
                    new_contour = np.append(reversed(set[i]), new_contour, axis=0)
                    del set[i]
                    break
                if neighbours(new_contour[0], set[i][-1]):
                    new_contour = np.append(set[i], new_contour, axis=0)
                    del set[i]
                    break
                if neighbours(new_contour[-1], set[i][0]):
                    new_contour = np.append(new_contour, set[i])
                    del set[i]
                    break
                if neighbours(new_contour[-1], set[i][-1]):
                    new_contour = np.append(new_contour, reversed(set[i]), axis=0)
                    del set[i]
                    break
        final_contours.append(new_contour)

    return final_contours


def get_edges(map_img, lower, upper):
    # create NumPy arrays from the boundaries
    lower = np.array(lower, dtype="uint8")
    upper = np.array(upper, dtype="uint8")

    # find the colors within the specified boundaries and apply the mask
    mask = cv2.inRange(map_img, lower, upper)
    _, thresh = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY)
    _, contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    contours = list(map(lambda x: x.reshape(np.delete(x.shape, 1)), contours))

    # Filter false contours
    CONTOUR_POINTS_THRESH = 100
    for i in range(len(contours) - 1, -1, -1):
        if len(contours[i]) < CONTOUR_POINTS_THRESH:
            del contours[i]

    for i in range(len(contours)):
        new_contour = []
        for j in range(0, len(contours[i]), FILTER_FACTOR):
            new_contour.append(contours[i][j])
        # Add the final point of the original contour
        if (len(contours[i]) - 1) % FILTER_FACTOR != 0:
            new_contour.append(contours[i][-1])
        contours[i] = np.array(new_contour)

    return contours


def get_lane_separators(map_img, road_edges, trim_intersection=True):
    # Get green regions contours
    GREEN_LOW_THRESH = [0,0,4]
    GREEN_HIGH_THRESH = [0,255,6]
    contours = get_edges(map_img, GREEN_LOW_THRESH, GREEN_HIGH_THRESH)

    # Trim road edge points from contours
    contours = trim_contour(contours, road_edges, roadedge_point)

    # Trim intersection contours
    if trim_intersection:
        contours = trim_contour(contours, map_img, white_neighbor)

    # Order points on the contours
    for i in range(len(contours)):
        cut_point = -1
        for j in range(1, len(contours[i])):
            if not neighbours(contours[i][j - 1], contours[i][j]):
                cut_point = j
                break
        if cut_point != -1:
            contours[i] = np.append(contours[i][cut_point:], contours[i][:cut_point], 0)

    contours = list(map(np.array, contours))

    return contours


def repair_contours(contours):
    global FILTER_FACTOR
    res_contours = []
    end_points = {}
    matched = {}

    for i in range(len(contours)):
        end_points[str(contours[i])] = (contours[i][0], contours[i][-1])

    old_filter_factor = FILTER_FACTOR
    FILTER_FACTOR = 3
    # Reorder points to have the line end points on the first and final position in the list
    for i in range(len(contours)):
        crack_point = -1
        for j in range(1,len(contours[i])):
            if not neighbours(contours[i][j - 1], contours[i][j]):
                crack_point = j
                break
        if crack_point != -1:
            contours[i] = np.append(contours[i][crack_point:], contours[i][:crack_point], axis=0)

    # For each contour, check if there is any other contour that could continue it
    for i in range(len(contours)):
        if str(contours[i]) in matched:
            continue
        match_found = False
        for j in range(i+1,len(contours)):
            if str(contours[j]) in matched:
                continue
            # End of the first is neighbor with start of the other
            if neighbours(end_points[str(contours[i])][1], end_points[str(contours[j])][0]):
                res_contours.append(np.append(contours[i], contours[j], axis=0))
                match_found = True
                matched[str(contours[j])] = 1
                break
            # End of the first is neighbor with end of the other
            elif neighbours(end_points[str(contours[i])][1], end_points[str(contours[j])][1]):
                res_contours.append(np.append(contours[i], list(reversed(contours[j])), axis=0))
                match_found = True
                matched[str(contours[j])] = 1
                break
            # Start of the first is neighbor with start of the other
            elif neighbours(end_points[str(contours[i])][0], end_points[str(contours[j])][0]):
                res_contours.append(np.append(list(reversed(contours[j])), contours[i], axis=0))
                match_found = True
                matched[str(contours[j])] = 1
                break
            # Start of the first is neighbor with end of the other
            elif neighbours(end_points[str(contours[i])][0], end_points[str(contours[j])][1]):
                res_contours.append(np.append(contours[j], contours[i], axis=0))
                match_found = True
                matched[str(contours[j])] = 1
                break
        if not match_found:
            res_contours.append(contours[i])

    FILTER_FACTOR = old_filter_factor

    return res_contours


# Gradient computetion functions
def adjust_grad(map_img, posx, posy, gx, gy):
    # Change the direction if it points towards the outside of the road
    newx = posx
    newy = posy
    SEARCH_DIST = 4
    while abs(int(newx) - posx) < SEARCH_DIST and abs(int(newy) - posy) < SEARCH_DIST:
        newx += gx
        newy += gy

    newx = int(newx)
    newy = int(newy)
    if np.all(map_img[newy][newx] == [0, 0, 0]):
        gx = -gx
        gy = -gy

    return gx, gy


def compute_gradient(index, edge, map_img):
    posx = edge[index][0]
    posy = edge[index][1]

    # Compute gradient as the mean of the slopes for lines determined with the neighbouring points
    INTERVAL_LEN = 4
    first_ind = index - INTERVAL_LEN
    last_ind = index + INTERVAL_LEN
    # Adjust the range over which to compute the gradient
    if first_ind < 0:
        last_ind -= first_ind
        first_ind = 0
    elif last_ind > len(edge) - 1:
        first_ind -= last_ind - len(edge) + 1
        last_ind = len(edge) - 1

    gradx = 0
    grady = 0
    for ind in range(first_ind, last_ind+1):
        if ind == index:
            continue
        px = edge[ind][0]
        py = edge[ind][1]
        # Points with same y coordinate
        if posy == py:
            gx, gy = 0, 1
            if (index - ind) * (posx - px) < 0:
                gy = -1
        # Points with the same x coordinate
        elif posx == px:
            gx, gy = 1, 0
            if (index - ind) * (posy - py) > 0:
                gx = -1
        else:
            slope = (posy - py) / (posx - px)
            incx = 1
            incy = -1 / slope
            if (index - ind) * (posy - py) > 0:
                incx = -incx
                incy = -incy
            norm = math.sqrt(incx**2 + incy**2)
            gx = incx / norm
            gy = incy / norm
            gx, gy = adjust_grad(map_img, posx, posy, gx, gy)
        gradx += gx
        grady += gy

    # Normalize gradient components
    norm = math.sqrt(gradx**2 + grady**2)
    gradx /= norm
    grady /= norm

    return gradx, grady


# Lane related functions
def extract_lanes(map_img, low_thresh, high_thresh):
    # Find the colors within the specified boundaries and apply the mask
    mask = cv2.inRange(map_img, low_thresh, high_thresh)
    _, thresh = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY)
    _, contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    contours = list(map(lambda x: x.reshape(np.delete(x.shape, 1)), contours))

    # Reduce contours to lines
    for i in range(len(contours)):
        repeating_point_left = -1
        for j in range(2,len(contours[i])):
            signy1 = np.sign(contours[i][j - 1][0] - contours[i][j - 2][0])
            signy2 = np.sign(contours[i][j][0] - contours[i][j - 1][0])
            signx1 = np.sign(contours[i][j - 1][1] - contours[i][j - 2][1])
            signx2 = np.sign(contours[i][j][1] - contours[i][j - 1][1])
            if signy1 != 0 and signy2 != 0 and signy1 != signy2:
                repeating_point_left = j
                break
            if signx1 != 0 and signx2 != 0 and signx1 != signx2:
                repeating_point_left = j
                break

        repeating_point_right = -1
        for j in range(len(contours[i]) - 2, -1, -1):
            signy1 = np.sign(contours[i][j - 1][0] - contours[i][j - 2][0])
            signy2 = np.sign(contours[i][j][0] - contours[i][j - 1][0])
            signx1 = np.sign(contours[i][j - 1][1] - contours[i][j - 2][1])
            signx2 = np.sign(contours[i][j][1] - contours[i][j - 1][1])
            if signy1 != 0 and signy2 != 0 and signy1 != signy2:
                repeating_point_right = j - 1
                break
            if signx1 != 0 and signx2 != 0 and signx1 != signx2:
                repeating_point_right = j - 1
                break

        if repeating_point_left != -1:
            if repeating_point_left != repeating_point_right + 1:
                contours[i] = np.append(contours[i][repeating_point_right:], contours[i][:repeating_point_left], axis=0)
            else:
                contours[i] = contours[i][:repeating_point_left]

    # Remove duplicate contours
    contour_points = {}
    contours_to_remove = []
    for i in range(len(contours)):
        for point in contours[i]:
            if str(point) not in contour_points:
                contour_points[str(point)] = 1
            else:
                contours_to_remove.append(i)
                break

    for i in range(len(contours_to_remove)-1, -1, -1):
        contours = np.delete(contours, contours_to_remove[i], axis=0)

    # Merge contours
    prev_len = 0
    while len(contours) != prev_len:
        prev_len = len(contours)
        contours = repair_contours(contours)

    # Filter lane points
    for i in range(len(contours)):
        new_contour = []
        for j in range(0,len(contours[i]),FILTER_FACTOR):
            new_contour.append(contours[i][j])
        # Add the final point of the original contour
        if (len(contours[i]) - 1) % FILTER_FACTOR != 0:
            new_contour.append(contours[i][-1])
        contours[i] = np.array(new_contour)

    # Set the the lane points in the correct direction
    for i in range(len(contours)):
        while True:
            # Choose random point on contour
            point_index = np.random.randint(len(contours[i]) - 1)
            gradx, grady = compute_gradient(point_index, contours[i], map_img)

            # Determine right distance
            dist_r = 0
            aux_point = [contours[i][point_index][0], contours[i][point_index][1]]
            while True:
                dist_r += 1
                aux_point[0] += gradx
                aux_point[1] += grady
                if np.all(map_img[int(aux_point[1]), int(aux_point[0])] == BLACK):
                    break
            # Determine left distance
            dist_l = 0
            aux_point = [contours[i][point_index][0], contours[i][point_index][1]]
            while True:
                dist_l += 1
                aux_point[0] -= gradx
                aux_point[1] -= grady
                if np.all(map_img[int(aux_point[1]), int(aux_point[0])] == BLACK):
                    break

            # If both distances are bigger than the maximum lane width, repeat
            if dist_l > MAX_LANE_PIXEL_WIDTH and dist_r > MAX_LANE_PIXEL_WIDTH:
                continue

            # If left is closer than right, reverse points
            if dist_l < dist_r:
                contours[i] = np.array(list(reversed(contours[i])))
            break

    return contours


def adjust_lane_direction(lanes, slanes, lane_type):
    global FILTER_FACTOR
    old_FILTER_FACTOR = FILTER_FACTOR
    FILTER_FACTOR *= 2
    for i in range(len(lanes)):
        # Find which lane end has an open straight lane end as neighbour
        for slane in slanes:
            # Skip closed straight lanes
            if neighbours(slane[0], slane[-1]):
                continue
            # First point in lane has neighbour
            if neighbours(lanes[i][0], slane[0]) or neighbours(lanes[i][0], slane[-1]):
                # Change lane direction if it is branching
                if lane_type == 'branching':
                    lanes[i] = list(reversed(lanes[i]))
                break
            # Last point in lane has neighbour
            elif neighbours(lanes[i][-1], slane[0]) or neighbours(lanes[i][-1], slane[-1]):
                # Change lane direction if it is merging
                if lane_type == 'merging':
                    lanes[i] = list(reversed(lanes[i]))
                break
    FILTER_FACTOR = old_FILTER_FACTOR

    lanes = list(map(np.array, lanes))
    return lanes


def read_lane_points(map_img, points):
    # Extract straight lanes
    LOW_STRAIGHT = (0, 0, 254)
    HIGH_STRAIGHT = (0, 11, 255)
    slanes = extract_lanes(map_img, LOW_STRAIGHT, HIGH_STRAIGHT)
    print("Finished straight lanes")
    # Extract left merging lanes
    LOW_LEFT_MERGING = (0, 199, 254)
    HIGH_LEFT_MERGING = (0, 201, 255)
    lmlanes = extract_lanes(map_img, LOW_LEFT_MERGING, HIGH_LEFT_MERGING)
    print("Finished left merging lanes")
    # Extract left branching lanes
    LOW_LEFT_BRANCHING = (0, 149, 254)
    HIGH_LEFT_BRANCHING = (0, 151, 255)
    lblanes = extract_lanes(map_img, LOW_LEFT_BRANCHING, HIGH_LEFT_BRANCHING)
    print("Finished left branching lanes")
    # Extract right merging lanes
    LOW_RIGHT_MERGING = (0, 49, 254)
    HIGH_RIGHT_MERGING = (0, 51, 255)
    rmlanes = extract_lanes(map_img, LOW_RIGHT_MERGING, HIGH_RIGHT_MERGING)
    print("Finished right merging lanes")
    # Extract right branching lanes
    LOW_RIGHT_BRANCHING = (0, 99, 254)
    HIGH_RIGHT_BRANCHING = (0, 101, 255)
    rblanes = extract_lanes(map_img, LOW_RIGHT_BRANCHING, HIGH_RIGHT_BRANCHING)
    print("Finished right branching lanes")

    # Adjust merging and branching lanes direction
    lmlanes = adjust_lane_direction(lmlanes, slanes, 'merging')
    lblanes = adjust_lane_direction(lblanes, slanes, 'branching')
    rmlanes = adjust_lane_direction(rmlanes, slanes, 'merging')
    rblanes = adjust_lane_direction(rblanes, slanes, 'branching')

    # Generate lane points
    all_lanes = np.append(slanes, lmlanes, axis=0)
    all_lanes = np.append(all_lanes, lblanes, axis=0)
    all_lanes = np.append(all_lanes, rmlanes, axis=0)
    all_lanes = np.append(all_lanes, rblanes, axis=0)
    PID = points[-1][2] + 1
    for lane in all_lanes:
        for point in lane:
            i = point[0]
            j = point[1]
            relative_loc = Density * np.array([i, j,])
            coord = relative_loc + MAP_OFFSET

            lat, long = transform_coord_to_lat_long(coord)

            points.append([i, j, PID, lat, long])
            PID += 1
    df_points = pd.DataFrame(points, columns=POINTS_COLUMNS)

    # Group lanes in a dicitionary
    lanes = {}
    lanes['straight'] = slanes
    lanes['left_merging'] = lmlanes
    lanes['left_branching'] = lblanes
    lanes['right_merging'] = rmlanes
    lanes['right_branching'] = rblanes

    return lanes


# Junction related functions
def detect_junctions(map_img):
    LOW_THRESH_JUNCTION = (255,0,255)
    HIGH_THRESH_JUNCTION = (255, 255, 255)
    mask = cv2.inRange(map_img, LOW_THRESH_JUNCTION, HIGH_THRESH_JUNCTION)
    _, thresh = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY)
    _, contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    contours = list(map(lambda x: x.reshape(np.delete(x.shape, 1)), contours))

    # Find the polygon for each junction
    junctions = []
    for contour in contours:
        junction = []
        # Find extreme points of the junction
        for point in contour:
            v = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            white_neighbors = 0
            for p in v:
                nx = p[0] + point[0]
                ny = p[1] + point[1]
                if np.all(map_img[ny, nx] == WHITE):
                    white_neighbors += 1
            # Found extreme point
            if white_neighbors <= 3:
                junction.append(point)

        # Find points that need to be moved to a road edge
        max_len = 0
        max_ind = 0
        max_nei_ind = 0
        for i in range(len(junction)):
            nei = (i + 1) % len(junction)
            if np.any(junction[i] == junction[nei]):
                dist = distance(junction[i], junction[nei])
                if max_len < dist:
                    max_len = dist
                    max_ind = i
                    max_nei_ind = nei

        # Extend points to the road edge
        dir = 1
        if junction[max_ind][0] == junction[max_nei_ind][0]:
            # Search left
            if np.all(map_img[junction[max_ind][1], junction[max_ind][0] + 1] == WHITE):
                dir = -1
            while not np.all(map_img[junction[max_ind][1], junction[max_ind][0]] == BLACK):
                junction[max_ind][0] += dir
            junction[max_nei_ind][0] = junction[max_ind][0]
        else:
            # Search up
            if np.all(map_img[junction[max_ind][1] + 1, junction[max_ind][0]] == WHITE):
                dir = -1
            while not np.all(map_img[junction[max_ind][1], junction[max_ind][0]] == BLACK):
                junction[max_ind][1] += dir
            junction[max_nei_ind][1] = junction[max_ind][1]
        junctions.append(junction)

    return junctions


def split_at_junctions(old_lanes, junctions):
    lanes = []
    for lane in old_lanes:
        # Reorder lane points such that the first one is at the entrance of a junction
        split_ind = -1
        for i in range(1, len(lane)):
            if split_ind >= 0:
                break
            for junction in junctions:
                if cv2.pointPolygonTest(np.array(junction), tuple(lane[i]), False) >= 0 and \
                    cv2.pointPolygonTest(np.array(junction), tuple(lane[i - 1]), False) < 0:
                    split_ind = i
                    break
        if split_ind != -1:
            lane = np.array(list(lane[split_ind:]) + list(lane[:split_ind]))

        # Split the lane into new lanes
        last_in_junction = True
        new_lane = []
        for i in range(len(lane)):
            point = lane[i]
            in_junction = False
            for junction in junctions:
                if cv2.pointPolygonTest(np.array(junction), tuple(point), False) >= 0:
                    in_junction = True
                    break
            if in_junction:
                new_lane.append(point)
                if not last_in_junction:
                    if new_lane:
                        lanes.append(np.array(new_lane))
                    new_lane = [point]
                last_in_junction = True
            else:
                if neighbours(point, lane[i - 1]):
                    new_lane.append(point)
                if last_in_junction or not neighbours(point, lane[i - 1]):
                    if new_lane:
                        lanes.append(np.array(new_lane))
                    new_lane = [point]
                last_in_junction = False

        # Add the final lane
        if split_ind != -1:
            new_lane.append(lane[0])
        lanes.append(new_lane)

    return lanes


def stick_lanes(lanes, slanes):
    global FILTER_FACTOR
    OLD_FILTER_FACTOR = FILTER_FACTOR
    FILTER_FACTOR *= 5

    for i in range(len(lanes)):
        # Stick to previous straight lane
        for slane in slanes:
            if neighbours(lanes[i][0], slane[-1]):
                lanes[i] = np.append([slane[-1]], lanes[i], axis=0)
        # Stick to next straight lane
        for slane in slanes:
            if neighbours(lanes[i][-1], slane[0]):
                lanes[i] = np.append(lanes[i], [slane[0]], axis=0)
    FILTER_FACTOR = OLD_FILTER_FACTOR


# Overlap related functions
def intersect(obj1, obj2):
    poly1 = Polygon(obj1.get_polygon())
    poly2 = Polygon(obj2.get_polygon())
    return poly1.intersects(poly2)

