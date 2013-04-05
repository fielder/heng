import struct

vertexes = []
linedefs = []
sidedefs = []
sectors = []
nodes = []
ssectors = []


def load(w, mapname):
    global vertexes
    global linedefs
    global sidedefs
    global sectors
    global nodes
    global ssectors

    start = w.lump_name_to_num[mapname]

    vertexes = _parseVERTEXES(w.readLumpFromOffset("VERTEXES", start))
    linedefs = _parseLINEDEFS(w.readLumpFromOffset("LINEDEFS", start))
    sidedefs = _parseSIDEDEFS(w.readLumpFromOffset("SIDEDEFS", start))
    sectors = _parseSECTORS(w.readLumpFromOffset("SECTORS", start))
    nodes = _parseNODES(w.readLumpFromOffset("NODES", start))
    ssectors = _parseSSECTORS(w.readLumpFromOffset("SSECTORS", start))

    print "%d VERTEXES" % len(vertexes)
    print "%d LINEDEFS" % len(linedefs)
    print "%d SIDEDEFS" % len(sidedefs)
    print "%d SECTORS" % len(sectors)
    print "%d NODES" % len(nodes)
    print "%d SSECTORS" % len(ssectors)

    print "Loaded %s" % mapname


def _pythonifyString(s):
    """
    Get rid of c-style string terminators.
    """

    return s.rstrip("\x00")


def _parseLINEDEFS(raw):
    ret = []

    for idx in xrange(0, len(raw), 14):
        lraw = raw[idx:idx + 14]

        v1, v2, flags, special, tag, sidenum0, sidenum1 = struct.unpack("<hhhhhhh", lraw)

        l = {}
        l["v1"] = v1
        l["v2"] = v2
        l["flags"] = flags
        l["special"] = special
        l["tag"] = tag
        l["sidenum"] = (sidenum0, sidenum1)

        ret.append(l)

    return ret


def _parseSIDEDEFS(raw):
    ret = []

    for idx in xrange(0, len(raw), 30):
        sraw = raw[idx:idx + 30]

        xoff, yoff, toptex, bottomtex, middletex, sector = struct.unpack("<hh8s8s8sh", sraw)

        s = {}
        s["xoff"] = xoff
        s["yoff"] = yoff
        s["toptexture"] = _pythonifyString(toptex)
        s["bottomtexture"] = _pythonifyString(bottomtex)
        s["midtexture"] = _pythonifyString(middletex)
        s["sector"] = sector

        ret.append(s)

    return ret


def _parseVERTEXES(raw):
    ret = []

    for idx in xrange(0, len(raw), 4):
        vraw = raw[idx:idx + 4]

        ret.append(struct.unpack("<hh", vraw))

    return ret


def _parseSECTORS(raw):
    ret = []

    for idx in xrange(0, len(raw), 26):
        sraw = raw[idx:idx + 26]

        f_height, c_height, f_tex, c_tex, light, special, tag = struct.unpack("<hh8s8shhh", sraw)

        s = {}
        s["floorheight"] = f_height
        s["ceilingheight"] = c_height
        s["floorpic"] = _pythonifyString(f_tex)
        s["ceilingpic"] = _pythonifyString(c_tex)
        s["lightlevel"] = light
        s["special"] = special
        s["tag"] = tag

        ret.append(s)

    return ret


def _parseNODES(raw):
    ret = []

    for idx in xrange(0, len(raw), 28):
        nraw = raw[idx:idx + 28]

        x, y, dx, dy, r_y_max, r_y_min, r_x_min, r_x_max, l_y_max, l_y_min, l_x_min, l_x_max, right, left = struct.unpack("<hhhhhhhhhhhhHH", nraw)

        r_bbox = { "mins": (r_x_min, r_y_min), "maxs": (r_x_max, r_y_max) }
        l_bbox = { "mins": (l_x_min, l_y_min), "maxs": (l_x_max, l_y_max) }

        s = {}
        s["x"] = x
        s["y"] = y
        s["dx"] = dx
        s["dy"] = dy
        s["bbox"] = (r_bbox, l_bbox)
        s["children"] = (right, left)

        ret.append(s)

    return ret


def _parseSSECTORS(raw):
    ret = []

    for idx in xrange(0, len(raw), 4):
        sraw = raw[idx:idx + 4]

        numsegs, firstseg = struct.unpack("<hh", sraw)

        s = {}
        s["numsegs"] = numsegs
        s["firstseg"] = firstseg

        ret.append(s)

    return ret
