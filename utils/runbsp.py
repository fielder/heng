import math
import copy

# original map objects from the WAD
vertexes = []
linedefs = []
sidedefs = []
sectors = []

# part of the BSP process
b_verts = []
b_lines = []

# output objects
o_verts = []


SIDE_EPSILON = 0.02

SIDE_ON    = 0 # lies on the line
SIDE_FRONT = 1
SIDE_BACK  = 2
SIDE_CROSS = 3


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


class BLine(object):

    def __init__(self, linedef, vertexes):
        self.linedef = linedef

        v1 = (float(vertexes[linedef["v1"]][0]), float(vertexes[linedef["v1"]][1]))
        v2 = (float(vertexes[linedef["v2"]][0]), float(vertexes[linedef["v2"]][1]))
        self.verts = (v1, v2)

        dx, dy = self.delta()
        normal = (dy, -dx)
        len_ = math.hypot(*normal)
        self.normal = (normal[0] / len_, normal[1] / len_)
        self.dist = dot(self.verts[0], self.normal)

    def delta(self):
        return (self.verts[1][0] - self.verts[0][0], self.verts[1][1] - self.verts[0][1])

    def isAxial(self):
        return math.fabs(self.normal[0]) == 1.0 or math.fabs(self.normal[1]) == 1.0

    def setV1(self, v):
        self.verts = (v, self.verts[1])

    def setV2(self, v):
        self.verts = (self.verts[0], v)

    def pointSide(self, p):
        d = dot(self.normal, p) - self.dist

        if math.fabs(d) < SIDE_EPSILON:
            side = SIDE_ON
        elif d < 0:
            side = SIDE_BACK
        elif d > 0:
            side = SIDE_FRONT
        else:
            raise Exception("shouldn't happen")

        return side

    def pointsSides(self, p1, p2):
        return (self.pointSide(p1), self.pointSide(p2))

    def lineSide(self, other):
        s1, s2 = self.pointsSides(other.verts[0], other.verts[1])

        if s1 == s2:
            side = s1
        elif s1 == SIDE_ON:
            side = s2
        elif s2 == SIDE_ON:
            side = s1
        else:
            side = SIDE_CROSS

        return side

    def _splitCrossingLine(self, other):
        """
        It's assumed other is known to cross.
        """

        d1 = dot(self.normal, other.verts[0]) - self.dist
        d2 = dot(self.normal, other.verts[1]) - self.dist

        frac = d1 / (d1 - d2)
        mid_x = self.verts[0][0] + frac * (self.verts[1][0] - self.verts[0][0]);
        mid_y = self.verts[0][1] + frac * (self.verts[1][1] - self.verts[0][1]);
        mid = (mid_x, mid_y)

        front = copy.copy(self)
        back = copy.copy(self)

        if d1 < 0:
            back.setV2(mid)
            front.setV1(mid)
        else:
            back.setV1(mid)
            front.setV2(mid)

        return (front, back)

    def splitLine(self, other):
        side = self.lineSide(other)

        if side == SIDE_FRONT:
            front = other
            back = None
        elif side == SIDE_BACK:
            front = None
            back = other
        elif side == SIDE_ON:
            front = None
            back = None
        else:
            front, back = self._splitCrossingLine(other)

        return (front, back)


def _isConvex(lines):
    #...
    return False


def _countSplits(lines, idx):
    # count the number of lines split
    # and count how many lines/pieces lie on both sides
    pass
    # or return the number of lines on either side, and
    # return the number of splits; it's assumed the caller
    # can add the splits to the sides to get a total count
    # no, will fail for colinear lines??
    return (numfront, numback, numsplit)


def _chooseNodeLine(lines):
    axial = []
    nonaxial = []

    for l in lines:
        if l.isAxial():
            axial.append(l)
        else:
            nonaxial.append(l)

    # choose an axial line with the least splits
    # if there isn't an axial, choose the one with least splits
    # choose the one that makes the most balanced tree
    #...

    return None


def _recursiveBSP(lines):
    if _isConvex(lines):
        pass
    else:
        node = _chooseNodeLine(lines)


def recursiveBSP(objs):
    global vertexes
    global linedefs
    global sidedefs
    global sectors
    global b_lines
    global b_verts
    global o_verts

    vertexes = objs["VERTEXES"]
    linedefs = objs["LINEDEFS"]
    sidedefs = objs["SIDEDEFS"]
    sectors = objs["SECTORS"]
    b_lines = []
    b_verts = []
    o_verts = []

#   b_verts = [(float(x), float(y)) for x, y in vertexes]
#   b_lines = [BLine(l) for l in linedefs]
    _recursiveBSP([BLine(l, vertexes) for l in linedefs])
