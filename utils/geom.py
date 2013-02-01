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
    def __init__(self, verts=None):
        # vertices, in CCW order
        if verts is not None:
            self.verts = copy.copy(verts)
        else:
            self.verts = []

        # References to lines that cut chopsurf edges; one reference
        # per vertex.
        # A ref will be None if no line cut and created that edge, but
        # was part of the original vertices.
        # Keyed by vertex tuple. The vertex indicates the starting
        # vertex of the cut edge.
        self.cutters = {v: None for v in self.verts}


def chopSurf(chopsurf, line):
#   chops = { SIDE_FRONT: ChopSurface2D(), SIDE_BACK: ChopSurface2D() }

    verts = copy.copy(chopsurf.verts)
    verts.append(verts[0]) # wrap-around case for easier looping
    dists = [dot2d(line.normal, v) - line.dist for v in verts]
    sides = [classifyDist(d) for d in dists]

    num_front = sides.count(SIDE_FRONT)
    num_back = sides.count(SIDE_BACK)
    num_cross = sides.count(SIDE_CROSS)
    num_on = sides.count(SIDE_ON)

    front_verts = []
    front_dists = []
    front_sides = []
    front_cutters = {}

    back_verts = []
    back_dists = []
    back_sides = []
    back_cutters = {}

    for idx in xrange(len(chopsurf.verts)):
        v1, v2 = verts[idx:idx + 2]
        d1, d2 = dists[idx:idx + 2]
        s1, s2 = sides[idx:idx + 2]
        cutter = chopsurf.cutters(v1)

        if s1 == SIDE_ON:
            front_verts.append(v1)
            front_dists.append(d1)
            front_sides.append(s1)
            front_cutters[v1] = cutter

            back_verts.append(v1)
            back_dists.append(d1)
            back_sides.append(s1)
            back_cutters[v1] = cutter
        #...

    #...

#   for side in (SIDE_FRONT, SIDE_BACK):
#       if len(chops[side].verts) < 3:
#           chops[side] = None

#   return (chops[SIDE_FRONT], chops[SIDE_BACK])


################################
################################
#       chops = { SIDE_FRONT: ChopSurface2D(), SIDE_BACK, ChopSurface2D() }

#       for idx in xrange(len(self.verts)):
#           v1, v2 = verts[idx:idx + 2]
#           d1, d2 = dists[idx:idx + 2]
#           s1, s2 = sides[idx:idx + 2]

#           if (s1, s2) == (SIDE_ON, SIDE_ON):
#               # the line colinear with an edge will set that edge's
#               # cutter to the line
#               cutter = 0
#           else:
#               cutter = self.cutters[idx]

#           if s1 == SIDE_ON:
#               chops[SIDE_FRONT].verts.append(v1)
#               chops[SIDE_FRONT].cutters.append(cutter)

#               chops[SIDE_BACK].verts.append(v1)
#               chops[SIDE_BACK].cutters.append(cutter)
#           else:
#               chops[s1].verts.append(v1)
#               chops[s1].cutters.append(cutter)

#           if (s1, s2) in ((SIDE_BACK, SIDE_FRONT), (SIDE_FRONT, SIDE_BACK)):
#               mid = lineFrac2D(v1, v2, d1 / (d1 - d2))

#               chops[SIDE_FRONT].verts.append(mid)
#               chops[SIDE_FRONT].cutters.append(cutter)

#               chops[SIDE_BACK].verts.append(mid)
#               chops[SIDE_BACK].cutters.append(cutter)

#       for idx, c in enumerate(chops[SIDE_FRONT].cutters):
#           if c == 0:
#               chops[SIDE_FRONT].cutters[idx] = line

#       for idx, c in enumerate(chops[SIDE_BACK].cutters):
#           if c == 0:
#               chops[SIDE_BACK].cutters[idx] = line

#       if len(chops[SIDE_FRONT]) < 3:
#           chops[SIDE_FRONT] = None
#       if len(chops[SIDE_BACK]) < 3:
#           chops[SIDE_BACK] = None

#       return (chops[SIDE_FRONT], chops[SIDE_BACK])
################################

#   def chopWithLine2(self, line):
#       verts = self.verts[:]
#       verts.append(verts[0]) # wrap-around case for easier looping
#       dists = [dot2d(line.normal, v) - line.dist for v in verts]
#       sides = [classifyDist(d) for d in dists]

#       if sides.count(SIDE_ON) > 2:
#           raise Exception("chopsurf with 3+ on points")

#       chops = { SIDE_FRONT: ChopSurface2D(), SIDE_BACK, ChopSurface2D() }

#       for idx in xrange(len(self.verts)):
#           v1, v2 = verts[idx:idx + 2]
#           d1, d2 = dists[idx:idx + 2]
#           s1, s2 = sides[idx:idx + 2]

#           if (s1, s2) == (SIDE_ON, SIDE_ON):
#               # the line colinear with an edge will set that edge's
#               # cutter to the line
#               cutter = 0
#           else:
#               cutter = self.cutters[idx]

#           if s1 == SIDE_ON:
#               chops[SIDE_FRONT].verts.append(v1)
#               chops[SIDE_FRONT].cutters.append(cutter)

#               chops[SIDE_BACK].verts.append(v1)
#               chops[SIDE_BACK].cutters.append(cutter)
#           else:
#               chops[s1].verts.append(v1)
#               chops[s1].cutters.append(cutter)

#           if (s1, s2) in ((SIDE_BACK, SIDE_FRONT), (SIDE_FRONT, SIDE_BACK)):
#               mid = lineFrac2D(v1, v2, d1 / (d1 - d2))

#               chops[SIDE_FRONT].verts.append(mid)
#               chops[SIDE_FRONT].cutters.append(cutter)

#               chops[SIDE_BACK].verts.append(mid)
#               chops[SIDE_BACK].cutters.append(cutter)

#       for idx, c in enumerate(chops[SIDE_FRONT].cutters):
#           if c == 0:
#               chops[SIDE_FRONT].cutters[idx] = line

#       for idx, c in enumerate(chops[SIDE_BACK].cutters):
#           if c == 0:
#               chops[SIDE_BACK].cutters[idx] = line

#       if len(chops[SIDE_FRONT]) < 3:
#           chops[SIDE_FRONT] = None
#       if len(chops[SIDE_BACK]) < 3:
#           chops[SIDE_BACK] = None

#       return (chops[SIDE_FRONT], chops[SIDE_BACK])

################################

#   for verts:
#       if v is on and vnext is on, node = -1
#       eles, node = input node

#       find side the new vertex/node will go (both sides if v is on the line)

#       add v & node to correct side (or both)

#       if v/vnext crosses, add midpoint to both sides w/ node of -1

#           if (s1, s2) in ((SIDE_FRONT, SIDE_BACK), (SIDE_BACK, SIDE_FRONT)):