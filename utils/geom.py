import math
import copy

SIDE_EPSILON = 0.02

SIDE_ON    = 0 # lies on the line
SIDE_FRONT = 1
SIDE_BACK  = 2
SIDE_CROSS = 3


def dot2d(a, b):
    return a[0] * b[0] + a[1] * b[1]


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
        d = dot2d(self.normal, p) - self.dist

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

    def _splitCrossingLine(self, other):
        """
        It's assumed other is known to cross.
        """

        d1 = dot2d(self.normal, other.verts[0]) - self.dist
        d2 = dot2d(self.normal, other.verts[1]) - self.dist

        frac = d1 / (d1 - d2)
        mid_x = other.verts[0][0] + frac * (other.verts[1][0] - other.verts[0][0]);
        mid_y = other.verts[0][1] + frac * (other.verts[1][1] - other.verts[0][1]);
        mid = (mid_x, mid_y)

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


class ChopSurface2D(object):
    def __init__(self):
        # in CCW order
        self.verts = []

        # one node reference for each chopsurf side
        self.nodes = []

    def setup(self, mins, maxs):
        a = 32.0
        v1 = (mins[0] - a, mins[1] - a)
        v2 = (mins[0] - a, maxs[1] + a)
        v3 = (maxs[0] + a, maxs[1] + a)
        v4 = (maxs[0] + a, mins[1] - a)
        self.verts = [v1, v2, v3, v4]

    def chop(self, line2d):
        #TODO: ...
        pass


class Bounds3D(object):
    def __init__(self):
        self.mins = [999999.0, 999999.0, 999999.0]
        self.maxs = [-999999.0, -999999.0, -999999.0]

    def __repr__(self):
        return repr((self.mins, self.maxs))

    def __getitem__(self, i):
        return (self.mins, self.maxs)[i]

    def update(self, other):
        if isinstance(other, Bounds3D):
            # other bounds
            for i in xrange(3):
                self.mins[i] = min(self.mins[i], other.mins[i])
                self.maxs[i] = max(self.maxs[i], other.maxs[i])
            return

        if isinstance(other[0], float) or isinstance(other[0], int):
            # single point
            points = [other]
        else:
            # list/tuple of points
            points = other

        for i in xrange(3):
            vals = [p[i] for p in points]
            self.mins[i] = float(min(self.mins[i], min(vals)))
            self.maxs[i] = float(max(self.maxs[i], max(vals)))
