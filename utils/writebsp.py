import struct

import wad


def _rawVert(v):
    return struct.pack("<fff", v[0], v[1], v[2])


def _rawPlane(p):
    normal = p[:3]
    dist = p[3]
    #FIXME: correctly set type and signbits
    type_ = 0
    signbits = 0x0
    return struct.pack("<ffffHH", normal[0], normal[1], normal[2], dist, type_, signbits)


def _rawEdge(e):
    return struct.pack("<II", e[0], e[1])


def _rawSurface(s):
    return struct.pack("<III", s["planenum"], s["firstedge"], s["numedges"])


def writeFile(mapname, path, objs):
    print ""
    print "Writing \"%s\" ..." % path

    lumps = []
    lumps.append((mapname, ""))

    # 3D vertices
    raw = ""
    for v in objs["vertexes"]:
        raw += _rawVert(v)
    lumps.append(("VERTEXES", raw))

    # Planes
    raw = ""
    for p in objs["planes"]:
        raw += _rawPlane(p)
    lumps.append(("PLANES", raw))

    # Edges
    raw = ""
    for e in objs["edges"]:
        raw += _rawEdge(e)
    lumps.append(("EDGES", raw))

    # Surface Edges
    raw = "".join([struct.pack("<I", se) for se in objs["surfedges"]])
    lumps.append(("S_EDGES", raw))

    # Surfaces
    raw = ""
    for s in objs["surfaces"]:
        raw += _rawSurface(s)
    lumps.append(("SURFACES", raw))

    #TODO: leafs
    #TODO: nodes

    # 2D vertices
    raw = ""
    for v in objs["verts_2d"]:
        raw += struct.pack("<ff", v[0], v[1])
    lumps.append(("VERTS_2D", raw))

    # 2D lines
    raw = ""
    for l in objs["lines_2d"]:
        raw += struct.pack("<ii", l[0], l[1])
    lumps.append(("LINES_2D", raw))

    # 2D leafs
    raw = ""
    for leaf in objs["leafs_2d"]:
        raw += struct.pack("<ii", leaf["firstline"], leaf["numlines"])
    lumps.append(("LEAFS_2D", raw))

    wad.writeWad(path, lumps)
