import math
import copy
import collections

#TODO: Create 2 blines for each side of a linedef and put each side
#      on the proper side of the plane
#      Might have to tie the 2 sides of a line such that splitting
#      one side doesn't create a t-junction

# original map objects from the WAD
vertexes = []
linedefs = []
sidedefs = []
sectors = []

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

    def pointsSides(self, points):
        return [self.pointSide(p) for p in points]

    def lineSide(self, other):
        s1, s2 = self.pointsSides( (other.verts[0], other.verts[1]) )

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
    """
    Check if a set of lines form a convex space. If 2 separate vertices
    lay on opposite sides of a line, it's non-convex.
    """

    for l in lines:
        sides = set()

        for other in lines:
            if l == other:
                continue

            sides.update(l.pointsSides(other.verts))

            if SIDE_FRONT in sides and SIDE_BACK in sides:
                return False

    return True


def _countSplits(lines, l):
    sides = [l.lineSide(ll) for ll in lines]

    front = sides.count(SIDE_FRONT)
    back = sides.count(SIDE_BACK)
    on = sides.count(SIDE_ON)
    cross = sides.count(SIDE_CROSS)

    return (front, back, on, cross)


ChoiseParams = collections.namedtuple("ChoiseParams", ["index", "axial", "front", "back", "on", "cross", "balance"])

#TODO: Probably check against a few different cutoffs; the idea is that
#      a lower cutoff (gives a better balanced tree) might be worth a
#      few extra splits.
IMBALANCE_CUTOFF = 0.15

def _chooseNodeLine(lines):
    len_ = float(len(lines))

    # sort lines by axial cases first
    axial = []
    nonaxial = []
    for l in lines:
        if l.isAxial():
            axial.append(l)
        else:
            nonaxial.append(l)
    lines = axial + nonaxial

    counts = []

    # find where each line lies with respect to each other
    for idx, l in enumerate(lines):
        front, back, on, cross = _countSplits(lines, l)
        counts.append( ChoiseParams(idx, l.isAxial(), front, back, on, cross, abs(front - back) / len_) )

    # sort the candidates by how well they divide the space; ideally
    # we would get a line that divides the space exactly in half
    by_balance = sorted(counts, key=lambda x: x.balance)
    by_balance_axial = filter(lambda x: x.axial, by_balance)
    by_balance_nonaxial = filter(lambda x: not x.axial, by_balance)

    best_axial = None
    if by_balance_axial:
        best_axial = by_balance_axial[0]
        for cp in by_balance_axial:
            if cp.balance > IMBALANCE_CUTOFF:
                break
            if cp.cross < best_axial.cross:
                best_axial = cp

    best_nonaxial = None
    if by_balance_nonaxial:
        best_nonaxial = by_balance_nonaxial[0]
        for cp in by_balance_nonaxial:
            if cp.balance > IMBALANCE_CUTOFF:
                break
            if cp.cross < best_nonaxial.cross:
                best_nonaxial = cp

    if best_axial:
        best = best_axial
    elif best_nonaxial:
        best = best_nonaxial
    else:
        # shouldn't happen
        raise Exception("no node chosen")

    if False:
        print best

    return lines[best.index]


def _recursiveBSP(lines):
    if True:
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
    global o_verts

    vertexes = objs["VERTEXES"]
    linedefs = objs["LINEDEFS"]
    sidedefs = objs["SIDEDEFS"]
    sectors = objs["SECTORS"]
    o_verts = []

    _recursiveBSP([BLine(l, vertexes) for l in linedefs])
