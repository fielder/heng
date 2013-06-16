import ctypes

from utils import vec

planes = []
edges = []
verts = []
polys = []


def _getVert(v):
    try:
        return verts.index(v)
    except ValueError:
        verts.append(v)
        return len(verts) - 1


def _getEdge(v1, v2):
    e = (v1, v2)
    try:
        ret = edges.index(e)
    except ValueError:
        backwards = (v2, v1)
        try:
            ret = edges.index(backwards)
            ret |= 0x80000000
        except ValueError:
            edges.append(e)
            ret = len(edges) - 1
    return ret


def _findPlane(plane):
    for idx, p in enumerate(planes):
        if vec.planeCompare(plane, p):
            return idx
    raise IndexError()


def addPoly(pverts):
    for idx in xrange(len(pverts)):
        a = pverts[idx] - pverts[0]
        b = pverts[(idx + 1) % len(pverts)] - pverts[0]
        normal = a.cross(b).normalized
        if normal != (0,0,0):
            break
    else:
        raise Exception("no normal for %s" % pverts)
    dist = normal.dot(pverts[0])
    plane = vec.Plane(normal, dist)

    try:
        plane_idx = _findPlane(plane)
        back_side_of_plane = False
    except IndexError:
        try:
            plane_idx = _findPlane(vec.Plane(-normal, -dist))
            back_side_of_plane = True
        except IndexError:
            planes.append(plane)
            plane_idx = len(planes) - 1
            back_side_of_plane = False

    v_idx = [_getVert(v) for v in pverts]
    with_wrap = v_idx + [v_idx[0]]

    edge_verts = zip(v_idx, with_wrap[1:])

    edge_idx = [_getEdge(v1, v2) for v1, v2 in edge_verts]

    poly = {}
    poly["plane_index"] = plane_idx
    poly["plane_back"] = back_side_of_plane
    poly["edges"] = edge_idx

    polys.append(poly)


VV = []
def _V(x, y, z):
    VV.append(vec.Vec3(x, y, z))
def _A(*vidx):
    addPoly([VV[idx] for idx in vidx])

_V(0, 0, 0)
_V(32, 0, 0)
_V(64, 0, 0)
_V(96, 0, 0)
_V(128, 0, 0)
_V(160, 0, 0)

_V(32, 32, 0)
_V(64, 32, 0)
_V(96, 32, 0)
_V(128, 32, 0)

_V(32, 96, 0)
_V(64, 96, 0)
_V(96, 96, 0)
_V(128, 96, 0)

_V(0, 128, 0)
_V(32, 128, 0)
_V(64, 128, 0)
_V(96, 128, 0)
_V(128, 128, 0)
_V(160, 128, 0)

_V(32, 160, 32)
_V(160, 160, 32)

_V(0, 0, 256)
_V(0, 128, 256)
_V(32, 160, 256)

_A(14, 0, 1, 6, 10, 15)
_A(6, 1, 2, 7)
_A(15, 10, 11, 16)
_A(16, 11, 7, 2, 3, 8, 12, 17)
_A(8, 3, 4, 9)
_A(17, 12, 13, 18)
_A(4, 5, 19, 18, 13, 9)
_A(14, 15, 16, 17, 18, 19, 21, 20)
_A(23, 22, 0, 14)
_A(24, 23, 14, 20)

################################################################
################################################################

MAP_VERSION = 1

import struct
import zipfile

class c_Vert(ctypes.Structure):
    _fields_ = [("xyz", ctypes.c_float * 3)]

class c_Plane(ctypes.Structure):
    _fields_ = [("normal",      ctypes.c_float * 3),
                ("dist",        ctypes.c_float),
                ("signbits",    ctypes.c_ushort),
                ("type",        ctypes.c_ushort)]

class c_Edge(ctypes.Structure):
    _fields_ = [("verts", ctypes.c_ushort * 2)]

class c_Poly(ctypes.Structure):
    _fields_ = [("plane",       ctypes.c_ushort),
                ("side",        ctypes.c_ushort),
                ("first_edge",  ctypes.c_ushort),
                ("num_edges",   ctypes.c_ushort),
                ("texinfo",     ctypes.c_ushort)]


PLANE_X = 0 # (1, 0, 0)
PLANE_Y = 1 # (0, 1, 0)
PLANE_Z = 2 # (0, 0, 1)
PLANE_0 = 3 # (+x, +y, +z)
PLANE_1 = 4 # (+x, +y, -z)
PLANE_2 = 5 # (+x, -y, +z)
PLANE_3 = 6 # (+x, -y, -z)


def planeSignBits(p):
    b = 0x0
    for i in xrange(3):
        if p.normal[i] < 0.0:
            b |= (1 << i)
    return b


def planeType(p):
    if p.normal == (1.0, 0.0, 0.0):
        return PLANE_X
    if p.normal == (0.0, 1.0, 0.0):
        return PLANE_Y
    if p.normal == (0.0, 0.0, 1.0):
        return PLANE_Z
    else:
# PLANE_0 = 3 # (+x, +y, +z)
# PLANE_1 = 4 # (+x, +y, -z)
# PLANE_2 = 5 # (+x, -y, +z)
# PLANE_3 = 6 # (+x, -y, -z)
        #TODO: ...
        return 99


def _planesString():
    strs = []
    for p in planes:
        n = p.normal
        dist = p.dist
        sbits = planeSignBits(p)
        type_ = planeType(p)
        s = struct.pack("<3ffHH", n[0], n[1], n[2], dist, sbits, type_)
        strs.append(s)
    return "".join(strs)


def _vertsString():
    strs = [struct.pack("<3f", v[0], v[1], v[2]) for v in verts]
    return "".join(strs)


def _edgesString():
    strs = [struct.pack("<2H", e[0], e[1]) for e in edges]
    return "".join(strs)


def _polyedgesString():
    polyedges = []
    for p in polys:
        p["first_edge"] = len(polyedges)
        for e in p["edges"]:
            ushort = ctypes.c_ushort(e & 0x7fffffff)
            if (e & 0x80000000) == 0x80000000:
                ushort.value |= 0x8000
            polyedges.append(ushort)

    strs = [struct.pack("<H", ushort.value) for ushort in polyedges]
    return "".join(strs)


def _polysString():
    strs = []

    for p in polys:
        plane_idx = p["plane_index"]
        side = {True: 1, False: 0}[p["plane_back"]]
        first_edge = p["first_edge"]
        num_edges = len(p["edges"])
        texinfo = 0
        s = struct.pack("<HHHHH", plane_idx, side, first_edge, num_edges, texinfo)

        strs.append(s)

    return "".join(strs)


def _headerString():
    return struct.pack("<4si", "HENG", MAP_VERSION)


with zipfile.ZipFile("out.zip", "w") as zh:
    zh.writestr("header", _headerString())
    zh.writestr("vertices", _vertsString())
    zh.writestr("planes", _planesString())
    zh.writestr("edges", _edgesString())
    zh.writestr("polyedges", _polyedgesString())
    zh.writestr("polys", _polysString())
