import struct

vertexes = []
linedefs = []
sidedefs = []
sectors = []


def load(w, mapname):
    global vertexes
    global linedefs
    global sidedefs
    global sectors

    start = w.lump_name_to_num[mapname]

    # negate each vertex y to match our coordinate system
    vertexes = [(x, -y) for x, y in _parseVERTEXES(w.readLumpFromOffset("VERTEXES", start))]

    linedefs = _parseLINEDEFS(w.readLumpFromOffset("LINEDEFS", start))
    sidedefs = _parseSIDEDEFS(w.readLumpFromOffset("SIDEDEFS", start))
    sectors = _parseSECTORS(w.readLumpFromOffset("SECTORS", start))

    print "%d VERTEXES" % len(vertexes)
    print "%d LINEDEFS" % len(linedefs)
    print "%d SIDEDEFS" % len(sidedefs)
    print "%d SECTORS" % len(sectors)
    print "%d NODES" % (len(w.readLumpFromOffset("NODES", start)) / 28)
    print "%d SSECTORS" % (len(w.readLumpFromOffset("SSECTORS", start)) / 4)

    print "Loaded %s" % mapname


def _pythonifyString(s):
    """
    Get rid of c-style string terminators.
    """

    if "\x00" in s:
        s = s[:s.index("\x00")]
    return s


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