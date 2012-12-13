import math
import copy

SIDE_EPSILON = 0.02

SIDE_ON    = 0 # lies on the line
SIDE_FRONT = 1
SIDE_BACK  = 2
SIDE_CROSS = 3


def dot2d(a, b):
    return a[0] * b[0] + a[1] * b[1]


def lineFrac2D(p1, p2, frac):
    return ( p1[0] + frac * (p2[0] - p1[0]),
             p1[1] + frac * (p2[1] - p1[1]) )


def lineFrac3D(p1, p2, frac):
    return ( p1[0] + frac * (p2[0] - p1[0]),
             p1[1] + frac * (p2[1] - p1[1]),
             p1[2] + frac * (p2[2] - p1[2]) )


def classifyDist(dist):
    if math.fabs(dist) < SIDE_EPSILON:
        side = SIDE_ON
    elif dist < 0:
        side = SIDE_BACK
    elif dist > 0:
        side = SIDE_FRONT
    else:
        raise Exception("shouldn't happen")
    return side


class Line2D(object):
    """
    A line segment on the 2D x-y plane.
    """

    def __init__(self, v1, v2):
        self.verts = (v1, v2)

        dx, dy = self.delta()
        normal = (dy, -dx)
        len_ = math.hypot(*normal)
        self.normal = (normal[0] / len_, normal[1] / len_)
        self.dist = dot2d(self.verts[0], self.normal)

    def delta(self):
        return (self.verts[1][0] - self.verts[0][0], self.verts[1][1] - self.verts[0][1])

    def isAxial(self):
        return math.fabs(self.normal[0]) == 1.0 or math.fabs(self.normal[1]) == 1.0

    def pointSide(self, p):
        return classifyDist(dot2d(self.normal, p) - self.dist)

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

    def _splitCrossingLine(self, other):
        """
        It's assumed other is known to cross.
        """

        v1 = other.verts[0]
        v2 = other.verts[1]
        d1 = dot2d(self.normal, v1) - self.dist
        d2 = dot2d(self.normal, v2) - self.dist
        mid = lineFrac2D(v1, v2, d1 / (d1 - d2))

        front = copy.copy(other)
        back = copy.copy(other)

        if d1 < 0:
            back.verts = (back.verts[0], mid)
            front.verts = (mid, front.verts[1])
        else:
            back.verts = (mid, back.verts[1])
            front.verts = (front.verts[0], mid)

        return (front, back)

    def splitLine(self, other):
        side = self.lineSide(other)

        front = None
        back = None
        on = None

        if side == SIDE_ON:
            on = other
        elif side == SIDE_FRONT:
            front = other
        elif side == SIDE_BACK:
            back = other
        elif side == SIDE_CROSS:
            front, back = self._splitCrossingLine(other)
        else:
            raise Exception("unknown side %s" % str(side))

        return (front, back, on)

    def splitLines(self, lines):
        front = []
        back = []
        on = []
        for l in lines:
            f, b, o = self.splitLine(l)
            if f:
                front.append(f)
            if b:
                back.append(b)
            if o:
                on.append(b)
        return (front, back, on)

    def countSides(self, lines):
        sides = [self.lineSide(l) for l in lines]

        front = sides.count(SIDE_FRONT)
        back = sides.count(SIDE_BACK)
        cross = sides.count(SIDE_CROSS)
        on = sides.count(SIDE_ON)

        return (front, back, cross, on)


class _Bounds(object):
    NUM_COMPONENTS = 1

    def __init__(self):
        self.mins = [999999.0] * self.NUM_COMPONENTS
        self.maxs = [-999999.0] * self.NUM_COMPONENTS

    def __repr__(self):
        return repr((self.mins, self.maxs))

    def __getitem__(self, i):
        return (self.mins, self.maxs)[i]

    def update(self, other):
        if isinstance(other, _Bounds):
            # other bounds
            for i in xrange(self.NUM_COMPONENTS):
                self.mins[i] = min(self.mins[i], other.mins[i])
                self.maxs[i] = max(self.maxs[i], other.maxs[i])
            return

        if isinstance(other[0], float) or isinstance(other[0], int):
            # single point
            points = [other]
        else:
            # list/tuple of points
            points = other

        for i in xrange(self.NUM_COMPONENTS):
            vals = [p[i] for p in points]
            self.mins[i] = float(min(self.mins[i], min(vals)))
            self.maxs[i] = float(max(self.maxs[i], max(vals)))


class Bounds2D(_Bounds):
    NUM_COMPONENTS = 2

    def toPoints(self):
        """
        In CCW order.
        """

        return [ (self.mins[0], self.mins[1]),
                 (self.mins[0], self.maxs[1]),
                 (self.maxs[0], self.maxs[1]),
                 (self.maxs[0], self.mins[1]) ]


class Bounds3D(_Bounds):
    NUM_COMPONENTS = 3


class ChopSurface2D(object):
    def __init__(self):
        # vertices, in CCW order
        self.verts = []

        # one node reference for each chopsurf side
        self.nodes = []

    def setup(self, verts):
        self.verts = verts[:]
        self.nodes = [None] * len(self.verts)

    def chopWithLine(self, line):
        verts = self.verts[:]
        verts.append(verts[0]) # wrap-around case for easier looping
        dists = [(dot2d(line.normal, v) - line.dist) for v in verts]
        sides = [classifyDist(d) for d in dists]

        front_chop = ChopSurface2D()
        back_chop = ChopSurface2D()

        for idx in xrange(len(self.verts)):
            node = self.nodes[idx]
            v1, v2 = verts[idx:idx + 2]
            d1, d2 = dists[idx:idx + 2]
            s1, s2 = sides[idx:idx + 2]

            if s1 in (SIDE_ON, SIDE_FRONT):
                front_chop.verts.append(v1)
                front_chop.nodes.append(node)

            if s1 in (SIDE_ON, SIDE_BACK):
                back_chop.verts.append(v1)
                back_chop.nodes.append(node)

#### ???
            if (s1, s2) == (SIDE_FRONT, SIDE_BACK):
                #...
                pass
            elif (s1, s2) == (SIDE_BACK, SIDE_FRONT):
                mid = lineFrac2D(v1, v2, d1 / (d1 - d2))

                back_chop.verts.append(mid)
                back_chop.nodes.append(line)

                front_chop.verts.append(mid)
                front_chop.nodes.append(node)
#### ???

        return front_chop, back_chop
