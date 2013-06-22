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

_V(64, 0, 300)
_V(32, 0, 300)
_V(32, 128, 300)
_V(64, 128, 300)

_A(3, 0, 1, 2)

################################################################
################################################################

MAP_VERSION = 2

import struct
import zipfile


def _planesString():
    strs = []
    for p in planes:
        n = p.normal
        dist = p.dist
        s = struct.pack("<3ff", n[0], n[1], n[2], dist)
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


with zipfile.ZipFile("out2.zip", "w") as zh:
    zh.writestr("header", _headerString())
    zh.writestr("vertices", _vertsString())
    zh.writestr("planes", _planesString())
    zh.writestr("edges", _edgesString())
    zh.writestr("polyedges", _polyedgesString())
    zh.writestr("polys", _polysString())
