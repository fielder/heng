import struct

import wad


def writeFile(mapname, path, objs):
    print ""
    print "Writing \"%s\" ..." % path

    lumps = []
    lumps.append((mapname, ""))

    #...

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
