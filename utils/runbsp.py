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

    def _updateV1(self, v):
        """
        Note it's assumed the new vertex is colinear with the old line.
        We don't update our normal.
        """

        self.verts = (v, self.verts[1])

    def _updateV2(self, v):
        """
        Note it's assumed the new vertex is colinear with the old line.
        We don't update our normal.
        """

        self.verts = (self.verts[0], v)

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
            back._updateV2(mid)
            front._updateV1(mid)
        else:
            back._updateV1(mid)
            front._updateV2(mid)

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


def _countSplits(lines, l):
    sides = [l.lineSide(ll) for ll in lines]

    front = sides.count(SIDE_FRONT)
    back = sides.count(SIDE_BACK)
    on = sides.count(SIDE_ON)
    cross = sides.count(SIDE_CROSS)

    return (front, back, on, cross)


def _chooseNodeLine(lines):
    axial = []
    nonaxial = []
    for l in lines:
        if l.isAxial():
            axial.append(l)
        else:
            nonaxial.append(l)
    lines = axial + nonaxial

    counts = []

    for idx, l in enumerate(lines):
        front, back, on, cross = _countSplits(lines, l)
        c = (idx, front, back, on, cross, abs(front - back) / float(len(lines)))
        counts.append(c)
    print sorted(counts, key=lambda x: x[5])

    # choose an axial line with the least splits
    # if there isn't an axial, choose the non-axial with least splits
    # choose the one that makes the most balanced tree
    #...

    return None


def _recursiveBSP(lines):
    if True:
#       print _countSplits(lines, lines[200])
        pass

    if _isConvex(lines):
        #TODO: emit a leaf
        pass
    else:
        node = _chooseNodeLine(lines)
        front = []
        back = []


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
