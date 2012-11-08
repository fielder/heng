"""
Extract a map's lumps out of one wad, into a new wad containing only
those lumps. Pretty much used to pull a map out of an IWAD.
"""

import sys

import wad

BASE_LUMPS = [ "THINGS",
               "LINEDEFS",
               "SIDEDEFS",
               "VERTEXES",
               "SEGS",
               "SSECTORS",
               "NODES",
               "SECTORS",
               "REJECT",
               "BLOCKMAP" ]

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print "usage: %s <iwad> <map> <map2> ..." % sys.argv[0]
        sys.exit(0)

    w = wad.Wad(sys.argv[1])

    for mapname in sys.argv[2:]:
        start = w.lump_name_to_num[mapname]

        lumps = [(lumpname, w.readLumpFromOffset(lumpname, start)) for lumpname in BASE_LUMPS]
        lumps.insert(0, (mapname, ""))

        outwad = "%s.wad" % mapname
        wad.writeWad(outwad, lumps)
        print "wrote", outwad
