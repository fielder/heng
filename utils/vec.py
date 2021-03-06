import math
import operator
import collections

SIDE_EPSILON = 1.0 / 32.0

SIDE_ON    = "on"
SIDE_FRONT = "front"
SIDE_BACK  = "back"
SIDE_CROSS = "cross"

PLANE_NORMAL_EPSILON = 0.00001
PLANE_DIST_EPSILON = 0.01

Plane = collections.namedtuple("Plane", ["normal", "dist"])


def _isScalar(x):
    return isinstance(x, float) or \
           isinstance(x, int) or \
           isinstance(x, long) or \
           isinstance(x, complex)

def _isXYZ(x):
    return isinstance(x, Vec3) or \
           ((isinstance(x, tuple) or isinstance(x, list)) and len(x) == 3)

def _isXY(x):
    return isinstance(x, Vec2) or \
           ((isinstance(x, tuple) or isinstance(x, list)) and len(x) == 2)

def _floatVals(vals):
    return tuple((float(v) for v in vals))

def _reprVerts(verts):
    return "{ " + " ".join([repr(v) for v in verts]) + " }"

def _parseVertsString(s):
    elts = s.strip().split()

    if elts.pop(0) != "{" or elts.pop() != "}":
        raise ValueError("invalid vertex list format")

    verts = []

    idx = 0
    while idx < len(elts):
        if elts[idx] != "(":
            raise ValueError("invalid vertex")
        start = idx
        while elts[idx] != ")":
            idx += 1
        idx += 1

        vals = [float(e) for e in elts[start + 1:idx - 1]]
        if len(vals) == 2:
            v = Vec2(vals[0], vals[1])
        elif len(vals) == 3:
            v = Vec3(vals[0], vals[1], vals[2])
        else:
            raise ValueError("invalid vertex \"%s\"" % str(vals))

        verts.append(v)

    return verts

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

def polyhedronFromPlanes(planes):
    polys = [Poly3D.newFromPlane(pl) for pl in planes]

    out = []
    for idx, p in enumerate(polys):
        for plidx, pl in enumerate(planes):
            if idx == plidx:
                # don't clip self
                continue
            front, p = p.splitWithPlane(pl)
            if not p:
                raise Exception("fully clipped a face")
        out.append(p)

    return out

def splitPoly(verts, normal, dist):
    """
    Will work with either 2d or 3d polys cutting with a line or a
    plane, respectively.
    """

    dists = [normal.dot(v) - dist for v in verts]
    sides = [classifyDist(d) for d in dists]

    num_on = sides.count(SIDE_ON)
    num_back = sides.count(SIDE_BACK)
    num_front = sides.count(SIDE_FRONT)

    if num_on == len(verts):
        return (None, None)
    elif num_back == 0:
        return (verts, None)
    elif num_front == 0:
        return (None, verts)

    # crosses the cutter, split it

    frontv = []
    backv = []

    for idx in xrange(len(verts)):
        v = verts[idx]
        dist = dists[idx]
        side = sides[idx]

        n_idx = (idx + 1) % len(verts)
        n_v = verts[n_idx]
        n_dist = dists[n_idx]
        n_side = sides[n_idx]

        if side == SIDE_ON:
            frontv.append(v)
            backv.append(v)
        elif side == SIDE_FRONT:
            frontv.append(v)
            if n_side == SIDE_BACK:
                mid = lineFrac(v, n_v, dist / (dist - n_dist))
                frontv.append(mid)
                backv.append(mid)
        elif side == SIDE_BACK:
            backv.append(v)
            if n_side == SIDE_FRONT:
                mid = lineFrac(v, n_v, dist / (dist - n_dist))
                frontv.append(mid)
                backv.append(mid)
        else:
            raise Exception("invalid side %s" % str(side))

    return (frontv, backv)

def identityMatrix():
    return ((1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0))

def multiplyMatrix(a, b):
    c_0_0 = a[0][0] * b[0][0] + a[0][1] * b[1][0] + a[0][2] * b[2][0]
    c_0_1 = a[0][0] * b[0][1] + a[0][1] * b[1][1] + a[0][2] * b[2][1]
    c_0_2 = a[0][0] * b[0][2] + a[0][1] * b[1][2] + a[0][2] * b[2][2]

    c_1_0 = a[1][0] * b[0][0] + a[1][1] * b[1][0] + a[1][2] * b[2][0]
    c_1_1 = a[1][0] * b[0][1] + a[1][1] * b[1][1] + a[1][2] * b[2][1]
    c_1_2 = a[1][0] * b[0][2] + a[1][1] * b[1][2] + a[1][2] * b[2][2]

    c_2_0 = a[2][0] * b[0][0] + a[2][1] * b[1][0] + a[2][2] * b[2][0]
    c_2_1 = a[2][0] * b[0][1] + a[2][1] * b[1][1] + a[2][2] * b[2][1]
    c_2_2 = a[2][0] * b[0][2] + a[2][1] * b[1][2] + a[2][2] * b[2][2]

    return ((c_0_0, c_0_1, c_0_2),
            (c_1_0, c_1_1, c_1_2),
            (c_2_0, c_2_1, c_2_2))

def anglesMatrix(angles, order="xyz"):
    c = math.cos(angles[0])
    s = math.sin(angles[0])
    x = ((1.0, 0.0, 0.0),
         (0.0,   c,  -s),
         (0.0,   s,   c))

    c = math.cos(angles[1])
    s = math.sin(angles[1])
    y = ((  c, 0.0,   s),
         (0.0, 1.0, 0.0),
         ( -s, 0.0,   c))

    c = math.cos(angles[2])
    s = math.sin(angles[2])
    z = ((  c,  -s, 0.0),
         (  s,   c, 0.0),
         (0.0, 0.0, 1.0))

    map_ = {"x": x, "y": y, "z": z}
    order = order.lower()

    tmp = multiplyMatrix(map_[order[0]], map_[order[1]])
    ret = multiplyMatrix(tmp, map_[order[2]])

    return ret

def planeCompare(a, b):
    return math.fabs(a.normal[0] - b.normal[0]) < PLANE_NORMAL_EPSILON and \
           math.fabs(a.normal[1] - b.normal[1]) < PLANE_NORMAL_EPSILON and \
           math.fabs(a.normal[2] - b.normal[2]) < PLANE_NORMAL_EPSILON and \
           math.fabs(a.dist - b.dist) < PLANE_DIST_EPSILON


class Vec3(object):
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
                raise ValueError("invalid value \"%s\"" % str(a))
        else:
            raise ValueError("invalid value \"%s\"" % str(args))

    def __repr__(self):
        x = repr(self._xyz[0])
        y = repr(self._xyz[1])
        z = repr(self._xyz[2])
        return "( %s %s %s )" % (x, y, z)

    def __len__(self):
        return len(self._xyz)

    def __eq__(self, other):
        return self._xyz[0] == other[0] and \
               self._xyz[1] == other[1] and \
               self._xyz[2] == other[2]

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def len(self):
        try:
            return self._len
        except AttributeError:
            self._len = math.sqrt(self._xyz[0] ** 2.0 + \
                                  self._xyz[1] ** 2.0 + \
                                  self._xyz[2] ** 2.0)
            return self._len

    @property
    def normalized(self):
        try:
            return self._normalized
        except AttributeError:
            l = self.len
            if l:
                self._normalized = self / l
            else:
                self._normalized = Vec3()
            return self._normalized

    def dot(self, other):
        return self._xyz[0] * other[0] + \
               self._xyz[1] * other[1] + \
               self._xyz[2] * other[2]

    def cross(self, other):
        return Vec3(self._xyz[1] * other[2] - self._xyz[2] * other[1],
                    self._xyz[2] * other[0] - self._xyz[0] * other[2],
                    self._xyz[0] * other[1] - self._xyz[1] * other[0])

    def sideOfPlane(self, plane):
        return classifyDist(self.dot(plane.normal) - plane.dist)

    def _binaryop(self, other, op):
        if _isScalar(other):
            return Vec3(op(self._xyz[0], other),
                        op(self._xyz[1], other),
                        op(self._xyz[2], other))
        elif _isXYZ(other):
            return Vec3(op(self._xyz[0], other[0]),
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
        try:
            return self._neg
        except AttributeError:
            self._neg = Vec3(-self._xyz[0],
                             -self._xyz[1],
                             -self._xyz[2])
            return self._neg

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

Vec3.ORIGIN = Vec3(0.0, 0.0, 0.0)
Vec3.X      = Vec3(1.0, 0.0, 0.0)
Vec3.Y      = Vec3(0.0, 1.0, 0.0)
Vec3.Z      = Vec3(0.0, 0.0, 1.0)


class Poly3D(object):
    """
    Vertices run in CCW order.
    """

    def __init__(self, other=None):
        self._verts = []

        if other:
            if isinstance(other, Poly3D):
                self._verts = other._verts[:]
            elif isinstance(other, list) or \
                 isinstance(other, tuple):
                self._verts = [Vec3(o) for o in other]
            else:
                raise ValueError("invalid value \"%s\"" % str(other))

        self._need_recalc = True

    def _recalc(self):
        if not self._need_recalc:
            return

        a = self._verts[1] - self._verts[0]
        b = self._verts[2] - self._verts[0]
        self._normal = a.cross(b).normalized
        self._dist = self._normal.dot(self._verts[0])
        self._axial = 1.0 in self._normal or -1.0 in self._normal

        self._need_recalc = False

    def __repr__(self):
        return _reprVerts(self._verts)

    def __len__(self):
        return len(self._verts)

    def __iter__(self):
        for v in self._verts:
            yield v

    def __getitem__(self, item):
        return self._verts[item]

    def append(self, v):
        self._verts.append(Vec3(v))
        self._need_recalc = True

    @property
    def normal(self):
        self._recalc()
        return self._normal

    @property
    def dist(self):
        self._recalc()
        return self._dist

    @property
    def axial(self):
        self._recalc()
        return self._axial

    def splitWithPlane(self, plane):
        f_verts, b_verts = splitPoly(self._verts, plane.normal, plane.dist)

        front = None
        back = None

        if f_verts:
            front = Poly3D(f_verts)
        if b_verts:
            back = Poly3D(b_verts)

        return (front, back)

    @classmethod
    def newFromString(cls, s):
        verts = _parseVertsString(s)
        if len(verts) < 3:
            raise ValueError("too few vertices")
        return cls(verts)

    @classmethod
    def newFromPlane(cls, plane):
        # First, find the up vector on the plane.
        # It is perpindicular to the normal, and points up if looking
        # directly down the normal.
        best = -99.0
        majoraxis = None
        for idx, val in enumerate(plane.normal):
            if math.fabs(val) > best:
                best = math.fabs(val)
                majoraxis = idx
        if majoraxis is None:
            raise Exception("no major axis for plane %s" % str(plane))

        if majoraxis == 0:
            up = Vec3(0, 1, 0)
        elif majoraxis == 1:
            up = Vec3(0, 0, 1)
        else:
            up = Vec3(0, 1, 0)
        # Have an appropriate up vector, project it onto the plane.
        dist = plane.normal.dot(up)
        up = (up - (plane.normal * dist)).normalized

        # can cross the normal and up orthogonal vectors to get the
        # right vector
        right = up.cross(plane.normal)

        up *= 8192.0
        right *= 8192.0

        origin = plane.normal * plane.dist

        verts = [ origin - right + up,
                  origin - right - up,
                  origin + right - up,
                  origin + right + up ]

        return cls(verts)


def _minVec(a, b):
    return Vec3( min(a[0], b[0]),
                 min(a[1], b[1]),
                 min(a[2], b[2]) )

def _maxVec(a, b):
    return Vec3( max(a[0], b[0]),
                 max(a[1], b[1]),
                 max(a[2], b[2]) )


class Bounds3D(object):
    def __init__(self, *args):
        self.mins = Vec3(99999.0, 99999.0, 99999.0)
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
        self.mins = Vec3(99999.0, 99999.0, 99999.0)
        self.maxs = -self.mins

    def update(self, other):
        if isinstance(other, Bounds3D):
            self.mins = _minVec(self.mins, other.mins)
            self.maxs = _maxVec(self.maxs, other.maxs)
        elif isinstance(other, Poly3D):
            for v in other:
                self.mins = _minVec(self.mins, v)
                self.maxs = _maxVec(self.maxs, v)
        elif _isXYZ(other):
            self.mins = _minVec(self.mins, other)
            self.maxs = _maxVec(self.maxs, other)
        else:
            raise ValueError("invalid value \"%s\"" % str(other))

    def __add__(self, other):
        ret = Bounds3D(self)
        ret.update(other)
        return ret

    def toPolys(self):
        v = []
        v.append(Vec3(self.mins[0], self.mins[1], self.mins[2])) # bottom
        v.append(Vec3(self.maxs[0], self.mins[1], self.mins[2])) # bottom
        v.append(Vec3(self.maxs[0], self.mins[1], self.maxs[2])) # bottom
        v.append(Vec3(self.mins[0], self.mins[1], self.maxs[2])) # bottom
        v.append(Vec3(self.mins[0], self.maxs[1], self.mins[2])) # top
        v.append(Vec3(self.maxs[0], self.maxs[1], self.mins[2])) # top
        v.append(Vec3(self.maxs[0], self.maxs[1], self.maxs[2])) # top
        v.append(Vec3(self.mins[0], self.maxs[1], self.maxs[2])) # top

        ret = []
        ret.append(Poly3D([v[3], v[0], v[1], v[2]])) # bottom
        ret.append(Poly3D([v[7], v[6], v[5], v[4]])) # top
        ret.append(Poly3D([v[7], v[3], v[2], v[6]])) # front
        ret.append(Poly3D([v[5], v[1], v[0], v[4]])) # back
        ret.append(Poly3D([v[4], v[0], v[3], v[7]])) # left
        ret.append(Poly3D([v[6], v[2], v[1], v[5]])) # right

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


class Vec2(object):
    """
    A 2d vector.
    """

    def __init__(self, *args):
        self._xy = (0.0, 0.0)

        if len(args) == 0:
            pass
        elif _isXY(args):
            # initialized with individual x,y components
            self._xy = _floatVals(args)
        elif len(args) == 1:
            a, = args
            if _isXY(a):
                self._xy = _floatVals(a)
            else:
                raise ValueError("invalid value \"%s\"" % str(a))
        else:
            raise ValueError("invalid value \"%s\"" % str(args))

    def __repr__(self):
        x = repr(self._xy[0])
        y = repr(self._xy[1])
        return "( %s %s )" % (x, y)

    def __len__(self):
        return len(self._xy)

    def __eq__(self, other):
        return self._xy[0] == other[0] and \
               self._xy[1] == other[1]

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def len(self):
        try:
            return self._len
        except AttributeError:
            self._len = math.hypot(self._xy[0], self._xy[1])
            return self._len

    @property
    def normalized(self):
        try:
            return self._normalized
        except AttributeError:
            l = self.len
            if l:
                self._normalized = self / l
            else:
                self._normalized = Vec2()
            return self._normalized

    def dot(self, other):
        return self._xy[0] * other[0] + \
               self._xy[1] * other[1]

    def sideOfLine(self, line):
        return classifyDist(self.dot(line.normal) - line.dist)

    def _binaryop(self, other, op):
        if _isScalar(other):
            return Vec2(op(self._xy[0], other),
                        op(self._xy[1], other))
        elif _isXY(other):
            return Vec2(op(self._xy[0], other[0]),
                        op(self._xy[1], other[1]))
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
        try:
            return self._neg
        except AttributeError:
            self._neg = Vec2(-self._xy[0],
                             -self._xy[1])
            return self._neg

    def __getitem__(self, item):
        return self._xy[item]

    @property
    def x(self):
        return self._xy[0]

    @property
    def y(self):
        return self._xy[1]

Vec2.ORIGIN = Vec2(0.0, 0.0)
Vec2.X      = Vec2(1.0, 0.0)
Vec2.Y      = Vec2(0.0, 1.0)


class Line2D(object):
    """
    A line segment on the 2D x-y plane.
    """

    def __init__(self, *args):
        self._verts = (Vec2(), Vec2())

        if len(args) == 0:
            pass
        elif len(args) == 2 and _isXY(args[0]) and _isXY(args[1]):
            # from 2 verts
            self._verts = (Vec2(args[0]), Vec2(args[1]))
        elif len(args) == 1 and isinstance(args[0], Line2D):
            # from another line
            self._verts = args[0]._verts
        else:
            raise ValueError("invalid values \"%s\"" % str(args))

        self._need_recalc = True

    def __repr__(self):
        return _reprVerts(self._verts)

    @classmethod
    def newFromString(cls, s):
        verts = _parseVertsString(s)
        if len(verts) != 2:
            raise ValueError("invalid vertex count")
        return cls(verts[0], verts[1])

    def _recalc(self):
        if not self._need_recalc:
            return

        self._delta  = self._verts[1] - self._verts[0]
        self._len    = self._delta.len
        self._axial  = self._delta[0] == 0.0 or self._delta[1] == 0.0
        self._normal = Vec2(self._delta[1], -self._delta[0]).normalized
        self._dist   = self._normal.dot(self._verts[0])

        self._need_recalc = False

    def __iter__(self):
        for v in self._verts:
            yield v

    def __getitem__(self, item):
        return self._verts[item]

    def __setitem__(self, item, val):
        if item == 0:
            self._verts = (Vec2(val), self._verts[1])
        elif item == 1:
            self._verts = (self._verts[0], Vec2(val))
        else:
            raise ValueError("invalid index %s" % item)
        self._need_recalc = True

    @property
    def normal(self):
        self._recalc()
        return self._normal

    @property
    def dist(self):
        self._recalc()
        return self._dist

    @property
    def delta(self):
        self._recalc()
        return self._delta

    @property
    def axial(self):
        self._recalc()
        return self._axial

    @property
    def len(self):
        self._recalc()
        return self._len

    def pointSide(self, p):
        dist = (p[0] * self.normal[0] + p[1] * self.normal[1]) - self.dist
        return classifyDist(dist)

    def lineSide(self, other, include_on=True):
        s1 = self.pointSide(other[0])
        s2 = self.pointSide(other[1])

        if s1 == s2:
            side = s1
        elif s1 == SIDE_ON:
            side = s2
        elif s2 == SIDE_ON:
            side = s1
        else:
            side = SIDE_CROSS

        if side == SIDE_ON and not include_on:
            # caller wants colinear lines to be classified as on the
            # front or back side, never on the line
            p = other[0] + (other.normal * 10.0)
            side = self.pointSide(p)
            if side == SIDE_ON:
                raise Exception("side check failed %s, other is %s" % (self, other))

        return side

    def _splitCrossingLine(self, other):
        """
        It's assumed other is known to cross.
        """

        A = other[0]
        B = other[1]

        dA = self.normal.dot(A) - self.dist
        dB = self.normal.dot(B) - self.dist

        frac = dA / (dA - dB)

        mid = Vec2( A[0] + frac * (B[0] - A[0]),
                    A[1] + frac * (B[1] - A[1]) )

        if dA < 0.0:
            back = Line2D(A, mid)
            front = Line2D(mid, B)
        else:
            back = Line2D(mid, B)
            front = Line2D(A, mid)

        return (front, back)

    def splitLine(self, other, include_on=True):
        side = self.lineSide(other, include_on=include_on)

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

    def splitLines(self, lines, include_on=True):
        front = []
        back = []
        on = []
        for l in lines:
            f, b, o = self.splitLine(l, include_on=include_on)
            if f:
                front.append(f)
            if b:
                back.append(b)
            if o:
                on.append(o)
        return (front, back, on)

    def countLinesSides(self, lines, include_on=True):
        sides = [self.lineSide(l, include_on=include_on) for l in lines]
        return ( sides.count(SIDE_FRONT),
                 sides.count(SIDE_BACK),
                 sides.count(SIDE_CROSS),
                 sides.count(SIDE_ON) )


class Poly2D(object):
    """
    Vertices run in CCW order.
    """

    def __init__(self, other=None):
        self._verts = []

        if other:
            if isinstance(other, Poly2D):
                self._verts = other._verts[:]
            elif isinstance(other, list) or \
                 isinstance(other, tuple):
                self._verts = [Vec2(o) for o in other]
            else:
                raise ValueError("invalid value \"%s\"" % str(other))

    def __repr__(self):
        return _reprVerts(self._verts)

    def __len__(self):
        return len(self._verts)

    def __iter__(self):
        for v in self._verts:
            yield v

    def __getitem__(self, item):
        return self._verts[item]

    def append(self, v):
        self._verts.append(Vec2(v))
        self._need_recalc = True

    def splitWithLine(self, line):
        f_verts, b_verts = splitPoly(self._verts, line.normal, line.dist)

        front = None
        back = None

        if f_verts:
            front = Poly2D(f_verts)
        if b_verts:
            back = Poly2D(b_verts)

        return (front, back)

    @classmethod
    def newFromString(cls, s):
        verts = _parseVertsString(s)
        if len(verts) < 3:
            raise ValueError("too few vertices")
        return cls(verts)
