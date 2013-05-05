import math
import operator

SIDE_EPSILON = 1.0 / 32.0

SIDE_ON    = 0
SIDE_FRONT = 1
SIDE_BACK  = 2
SIDE_CROSS = 3

PITCH = 0
YAW   = 1
ROLL  = 2

def _isScalar(x):
    return isinstance(x, float) or \
           isinstance(x, int) or \
           isinstance(x, long) or \
           isinstance(x, complex)

def _isXYZ(x):
    return isinstance(x, Vec) or \
           ((isinstance(x, tuple) or isinstance(x, list)) and len(x) == 3)

def _floatVals(vals):
    return tuple((float(v) for v in vals))

def classifyDist(d):
    if math.fabs(d) < SIDE_EPSILON:
        return SIDE_ON
    elif d < 0.0:
        return SIDE_BACK
    elif d > 0.0:
        return SIDE_FRONT

    raise Exception("shouldn't happen")

def lineFrac(a, b, frac):
    return a + (b - a) * frac

def minVec(a, b):
    return Vec( min(a[0], b[0]),
                min(a[1], b[1]),
                min(a[2], b[2]) )

def maxVec(a, b):
    return Vec( max(a[0], b[0]),
                max(a[1], b[1]),
                max(a[2], b[2]) )


class Vec(object):
    """
    A 3d vector.
    """

    def __init__(self, *args):
        self._xyz = (0.0, 0.0, 0.0)

        if len(args) == 0:
            pass
        elif _isXYZ(args):
            # initialized with individual x,y,z components
            self._xyz = _floatVals(args)
        elif len(args) == 1:
            a, = args
            if _isXYZ(a):
                self._xyz = _floatVals(a)
            else:
                raise TypeError("invalid value \"%s\"" % str(a))
        else:
            raise ValueError("invalid value \"%s\"" % str(args))

    def __str__(self):
        return "( %g %g %g )" % self._xyz

    def __repr__(self):
        return repr(self._xyz)

    def __len__(self):
        return len(self._xyz)

    @property
    def len(self):
        return math.sqrt(self.dot(self))

    @property
    def normalized(self):
        l = self.len
        if l:
            return self / l
        else:
            return Vec()

    def dot(self, other):
        return self._xyz[0] * other[0] + \
               self._xyz[1] * other[1] + \
               self._xyz[2] * other[2]

    def cross(self, other):
        return Vec(self._xyz[1] * other[2] - self._xyz[2] * other[1],
                   self._xyz[2] * other[0] - self._xyz[0] * other[2],
                   self._xyz[0] * other[1] - self._xyz[1] * other[0])

    def sideOfPlane(self, plane):
        return classifyDist(self.dot(plane.normal) - plane.dist)

    def _binaryop(self, other, op):
        if _isScalar(other):
            return Vec(op(self._xyz[0], other),
                       op(self._xyz[1], other),
                       op(self._xyz[2], other))
        elif _isXYZ(other):
            return Vec(op(self._xyz[0], other[0]),
                       op(self._xyz[1], other[1]),
                       op(self._xyz[2], other[2]))
        else:
            raise TypeError("invalid operand %s" % type(other))

    def __add__(self, other):
        return self._binaryop(other, operator.add)

    def __sub__(self, other):
        return self._binaryop(other, operator.sub)

    def __mul__(self, other):
        return self._binaryop(other, operator.mul)

    def __div__(self, other):
        return self._binaryop(other, operator.div)

    def __neg__(self):
        return Vec(-self._xyz[0],
                   -self._xyz[1],
                   -self._xyz[2])

    def __getitem__(self, item):
        return self._xyz[item]

    @property
    def x(self):
        return self._xyz[0]

    @property
    def y(self):
        return self._xyz[1]

    @property
    def z(self):
        return self._xyz[2]

Vec.ORIGIN = Vec(0.0, 0.0, 0.0)
Vec.X      = Vec(1.0, 0.0, 0.0)
Vec.Y      = Vec(0.0, 1.0, 0.0)
Vec.Z      = Vec(0.0, 0.0, 1.0)


class Poly(object):
    """
    Vertices run in CCW order.
    """

    def __init__(self, other=None):
        self.verts = []

        if other:
            if isinstance(other, Poly):
                self.verts = other.verts[:]
            elif isinstance(other, list) or \
                 isinstance(other, tuple):
                self.verts = other[:]
            else:
                raise ValueError("invalid value \"%s\"" % str(other))

    def __str__(self):
        return " ".join([str(v) for v in self.verts])

################################################################
    def splitWithPlane(self, plane):
        pnormal = plane.normal
        pdist = plan.dist
        count = len(self.verts)

        dists = [v.dot(pnormal) - pdist for v in self.verts]
        sides = [classifyDist(d) for d in dists]

        on = sides.count(SIDE_ON)
        front = sides.count(SIDE_FRONT)
        back = sides.count(SIDE_BACK)

        if on == count:
            return (None, None)
        elif back == 0:
            return (Poly(self), None)
        elif front == 0:
            return (None, Poly(self))

        frontv = []
        backv = []

        #...
        #...

        return (front, back)
################################################################

    @property
    def normal(self):
        a = self.verts[1] - self.verts[0]
        b = self.verts[2] - self.verts[0]
        return a.cross(b).normalized

    @property
    def dist(self):
        return self.normal.dot(self.verts[0])


class Bounds(object):
    def __init__(self, *args):
        self.mins = Vec(99999.0, 99999.0, 99999.0)
        self.maxs = -self.mins

        if args:
            if len(args) == 3:
                # init from x,y,z values
                other = args
            elif len(args) == 1:
                # init from a bounds, poly, or a point
                other, = args
            else:
                raise ValueError("invalid value \"%s\"" % str(args))
            self.update(other)

    def clear(self):
        self.mins = Vec(99999.0, 99999.0, 99999.0)
        self.maxs = -self.mins

    def update(self, other):
        if isinstance(other, Bounds):
            self.mins = minVec(self.mins, other.mins)
            self.maxs = maxVec(self.maxs, other.maxs)
        elif isinstance(other, Poly):
            for v in other.verts:
                self.mins = minVec(self.mins, v)
                self.maxs = maxVec(self.maxs, v)
        elif _isXYZ(other):
            self.mins = minVec(self.mins, other)
            self.maxs = maxVec(self.maxs, other)
        else:
            raise ValueError("invalid value \"%s\"" % str(other))

    def __add__(self, other):
        ret = Bounds(self)
        ret.update(other)
        return ret

    def toPolys(self):
        v = []
        v.append(Vec(self.mins[0], self.mins[1], self.mins[2])) # bottom
        v.append(Vec(self.maxs[0], self.mins[1], self.mins[2])) # bottom
        v.append(Vec(self.maxs[0], self.mins[1], self.maxs[2])) # bottom
        v.append(Vec(self.mins[0], self.mins[1], self.maxs[2])) # bottom
        v.append(Vec(self.mins[0], self.maxs[1], self.mins[2])) # top
        v.append(Vec(self.maxs[0], self.maxs[1], self.mins[2])) # top
        v.append(Vec(self.maxs[0], self.maxs[1], self.maxs[2])) # top
        v.append(Vec(self.mins[0], self.maxs[1], self.maxs[2])) # top

        ret = []
        ret.append(Poly([v[3], v[0], v[1], v[2]])) # bottom
        ret.append(Poly([v[7], v[6], v[5], v[4]])) # top
        ret.append(Poly([v[7], v[3], v[2], v[6]])) # front
        ret.append(Poly([v[5], v[1], v[0], v[4]])) # back
        ret.append(Poly([v[4], v[0], v[3], v[7]])) # left
        ret.append(Poly([v[6], v[2], v[1], v[5]])) # right

        return ret

    def testLine(self, v1, v2):
        all_axis = set([0, 1, 2])
        for ax in all_axis:
            for d1, d2 in ( (v1[ax] - self.maxs[ax],
                             v2[ax] - self.maxs[ax]),
                            (self.mins[ax] - v1[ax],
                             self.mins[ax] - v2[ax]) ):
                if d1 >= SIDE_EPSILON and d2 <= -SIDE_EPSILON:
                    p = lineFrac(v1, v2, d1 / (d1 - d2))
                    o1, o2 = all_axis - set([ax])
                    if p[o1] > self.mins[o1] and p[o1] < self.maxs[o1] and \
                       p[o2] > self.mins[o2] and p[o2] < self.maxs[o2]:
                        return p
        return None

        #NOTE: The above is a shortened, less-readable, version of the
        #      following implementation.

        # vertical side, facing +z
        d1 = v1[2] - self.maxs[2]
        d2 = v2[2] - self.maxs[2]
        if d1 >= SIDE_EPSILON and d2 <= -SIDE_EPSILON:
            p = lineFrac(v1, v2, d1 / (d1 - d2))
            if p[0] > self.mins[0] and p[0] < self.maxs[0] and \
               p[1] > self.mins[1] and p[1] < self.maxs[1]:
                return p

        # vertical side, facing -z
        d1 = self.mins[2] - v1[2]
        d2 = self.mins[2] - v2[2]
        if d1 >= SIDE_EPSILON and d2 <= -SIDE_EPSILON:
            p = lineFrac(v1, v2, d1 / (d1 - d2))
            if p[0] > self.mins[0] and p[0] < self.maxs[0] and \
               p[1] > self.mins[1] and p[1] < self.maxs[1]:
                return p

        # vertical side, facing +x
        d1 = v1[0] - self.maxs[0]
        d2 = v2[0] - self.maxs[0]
        if d1 >= SIDE_EPSILON and d2 <= -SIDE_EPSILON:
            p = lineFrac(v1, v2, d1 / (d1 - d2))
            if p[2] > self.mins[2] and p[2] < self.maxs[2] and \
               p[1] > self.mins[1] and p[1] < self.maxs[1]:
                return p

        # vertical side, facing -x
        d1 = self.mins[0] - v1[0]
        d2 = self.mins[0] - v2[0]
        if d1 >= SIDE_EPSILON and d2 <= -SIDE_EPSILON:
            p = lineFrac(v1, v2, d1 / (d1 - d2))
            if p[2] > self.mins[2] and p[2] < self.maxs[2] and \
               p[1] > self.mins[1] and p[1] < self.maxs[1]:
                return p

        # horizontal side, facing +y
        d1 = v1[1] - self.maxs[1]
        d2 = v2[1] - self.maxs[1]
        if d1 >= SIDE_EPSILON and d2 <= -SIDE_EPSILON:
            p = lineFrac(v1, v2, d1 / (d1 - d2))
            if p[2] > self.mins[2] and p[2] < self.maxs[2] and \
               p[0] > self.mins[0] and p[0] < self.maxs[0]:
                return p

        # horizontal side, facing -y
        d1 = self.mins[1] - v1[1]
        d2 = self.mins[1] - v2[1]
        if d1 >= SIDE_EPSILON and d2 <= -SIDE_EPSILON:
            p = lineFrac(v1, v2, d1 / (d1 - d2))
            if p[2] > self.mins[2] and p[2] < self.maxs[2] and \
               p[0] > self.mins[0] and p[0] < self.maxs[0]:
                return p

        return None
