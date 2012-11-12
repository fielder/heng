import math

PITCH = 0
YAW   = 1
ROLL  = 2

# VEC_EPSILON = 0.001
# 
# PLANE_X		= 0 # normal lies on x axis
# PLANE_Y		= 1 # normal lies on y axis
# PLANE_Z		= 2 # normal lies on z axis
# PLANE_NEAR_X	= 3 # normal is closest to PLANE_X
# PLANE_NEAR_Y	= 4 # normal is closest to PLANE_Y
# PLANE_NEAR_Z	= 5 # normal is closest to PLANE_Z
# 
# PLANE_DIST_EPSILON = 0.01
# PLANE_NORMAL_EPSILON = 0.00001

def vecInverse(a):
    return (-a[0], -a[1], -a[2])

def vecAdd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

def vecSub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def vecDot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

# def vecCross(a, b):
# 	cx = a[1] * b[2] - a[2] * b[1]
# 	cy = a[2] * b[0] - a[0] * b[2]
# 	cz = a[0] * b[1] - a[1] * b[0]
# 	return (cx, cy, cz)

def vecLen(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])

def vecScale(v, s):
    return (v[0] * s, v[1] * s, v[2] * s)

# def vecCompare(a, b):
# 	if math.fabs(a[0] - b[0]) > VEC_EPSILON:
# 		return False
# 	if math.fabs(a[1] - b[1]) > VEC_EPSILON:
# 		return False
# 	if math.fabs(a[2] - b[2]) > VEC_EPSILON:
# 		return False
# 	return True

def vecNormalize(v):
    l = vecLen(v)
    if l == 0.0:
        return (0.0, 0.0, 0.0)
    return vecScale(v, 1.0 / l)

# def vecSignBits(v):
# 	s = 0
# 	if v[0] < 0:
# 		s |= 0x1
# 	if v[1] < 0:
# 		s |= 0x2
# 	if v[2] < 0:
# 		s |= 0x4
# 	return s
# 
# def planeType(normal):
# 	if normal[0] == 1.0 or normal[0] == -1.0:
# 		return PLANE_X
# 	if normal[1] == 1.0 or normal[1] == -1.0:
# 		return PLANE_Y
# 	if normal[2] == 1.0 or normal[2] == -1.0:
# 		return PLANE_Z
# 
# 	ax = math.fabs(normal[0])
# 	ay = math.fabs(normal[1])
# 	az = math.fabs(normal[2])
# 
# 	if ax >= ay and ax >= az:
# 		return PLANE_NEAR_X
# 	if ay >= ax and ay >= az:
# 		return PLANE_NEAR_Y
# 	return PLANE_NEAR_Z
# 
# def planeCompare(normalA, distA, normalB, distB):
# 	return	math.fabs(normalA[0] - normalB[0]) < PLANE_NORMAL_EPSILON and \
# 		math.fabs(normalA[1] - normalB[1]) < PLANE_NORMAL_EPSILON and \
# 		math.fabs(normalA[2] - normalB[2]) < PLANE_NORMAL_EPSILON and \
# 		math.fabs(distA - distB) < PLANE_DIST_EPSILON
# 
# def planeSnappedNormal(normal):
# 	if math.fabs(normal[0] - 1.0) < PLANE_NORMAL_EPSILON:
# 		return (1.0, 0.0, 0.0)
# 	if math.fabs(normal[0] - -1.0) < PLANE_NORMAL_EPSILON:
# 		return (-1.0, 0.0, 0.0)
# 
# 	if math.fabs(normal[1] - 1.0) < PLANE_NORMAL_EPSILON:
# 		return (0.0, 1.0, 0.0)
# 	if math.fabs(normal[1] - -1.0) < PLANE_NORMAL_EPSILON:
# 		return (0.0, -1.0, 0.0)
# 
# 	if math.fabs(normal[2] - 1.0) < PLANE_NORMAL_EPSILON:
# 		return (0.0, 0.0, 1.0)
# 	if math.fabs(normal[2] - -1.0) < PLANE_NORMAL_EPSILON:
# 		return (0.0, 0.0, -1.0)
# 
# 	return normal
# 
# def planeSnappedDist(dist):
# 	rounded = math.floor(dist + 0.5)
# 	if math.fabs(dist - rounded) < PLANE_DIST_EPSILON:
# 		dist = rounded
# 	return dist
# 
# def planeSnap(normal, dist):
# 	return (planeSnappedNormal(normal), planeSnappedDist(dist))
# 
# def boundsClear(mins, maxs):
# 	mins[0], mins[1], mins[2] = 99999, 99999, 99999
# 	maxs[0], maxs[1], maxs[2] = -99999, -99999, -99999
# 
# def boundsUpdate(mins, maxs, v):
# 	for i in xrange(3):
# 		if v[i] < mins[i]:
# 			mins[i] = v[i]
# 		if v[i] > maxs[i]:
# 			maxs[i] = v[i]
