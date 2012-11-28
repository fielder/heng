import math
import copy

SIDE_EPSILON = 0.02

SIDE_ON    = 0 # lies on the line
SIDE_FRONT = 1
SIDE_BACK  = 2
SIDE_CROSS = 3


def dot(a, b):
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
        """
        Find which side other lies on. Note if the other line is
        colinear, we use the other's normal to determine whether
        it's on our front or back side.
        """

        s1, s2 = self.pointsSides( (other.verts[0], other.verts[1]) )

        if s1 == s2:
            if s1 == SIDE_ON:
                x = other.verts[0][0] + other.normal[0] * 8.0
                y = other.verts[0][1] + other.normal[1] * 8.0
                side = self.pointSide((x, y))
            else:
                # both on one side
                side = s1
        elif s1 == SIDE_ON:
            side = s2
        elif s2 == SIDE_ON:
            side = s1
        else:
            side = SIDE_CROSS

        if side == SIDE_ON:
            # shouldn't happen
            raise Exception("lineSide() gave ON")

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
            back.verts = (back.verts[0], mid)
            front.verts = (mid, front.verts[1])
        else:
            back.verts = (mid, back.verts[1])
            front.verts = (front.verts[0], mid)

        return (front, back)

    def splitLine(self, other):
        side = self.lineSide(other)

        if side == SIDE_FRONT:
            front = other
            back = None
        elif side == SIDE_BACK:
            front = None
            back = other
        else:
            front, back = self._splitCrossingLine(other)

        return (front, back)

    def splitLines(self, lines):
        front = []
        back = []
        for l in lines:
            f, b = self.splitLine(l)
            if f:
                front.append(f)
            if b:
                back.append(b)
        return (front, back)

    def countSides(self, lines):
        sides = [self.lineSide(l) for l in lines]

        front = sides.count(SIDE_FRONT)
        back = sides.count(SIDE_BACK)
        cross = sides.count(SIDE_CROSS)

        return (front, back, cross)
