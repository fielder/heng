"""
Merge 2 wads. Specifically, merge a single map wad and its glBSP'ed wad.
"""

import os
import sys

import wad

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print "usage: %s <map_wad> <glbsp_wad>" % sys.argv[0]
        sys.exit(0)

    if os.path.splitext(sys.argv[1])[1].upper() == ".WAD":
        wad_path = sys.argv[1]
        glwad_path = sys.argv[2]
    else:
        wad_path = sys.argv[2]
        glwad_path = sys.argv[1]

    w = wad.Wad(wad_path)
    glw = wad.Wad(glwad_path)

    w_lumps = [(l.name, w.readLump(l)) for l in w.lumps]
    glw_lumps = [(l.name, glw.readLump(l)) for l in glw.lumps]

    outwad = wad_path

    wad.writeWad(outwad, w_lumps + glw_lumps)

    print "wrote", outwad
