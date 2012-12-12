import sys

import wad
import inmap
import runbsp
import buildmap
#import writebsp


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "usage: %s <iwad> <mapname>" % sys.argv[0]
        sys.exit(0)
    w = wad.Wad(sys.argv[1])

    for mapname in sys.argv[2:]:
        inmap.load(w, mapname)

        runbsp.runBSP()
        buildmap.buildMap()
#       writebsp.writeFile(mapname, "%s.wad" % mapname)
