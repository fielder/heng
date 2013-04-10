#!/usr/bin/env python

import sys

import wad
import inmap
import runbsp
#import buildmap
#import writebsp


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "usage: %s <wad> [<mapname>]" % sys.argv[0]
        sys.exit(0)
    w = wad.Wad(sys.argv[1])

    if len(sys.argv) > 2:
        mapnames = sys.argv[2:]
    else:
        # no map name given; let user be lazy and auto-detect it
        #TODO: could be done more intelligently
        if len(w.lumps) == 11 and w.lumps[0].size == 0:
            mapnames = [w.lumps[0].name]
        else:
            raise Exception("unable to auto-detect map")

    for mapname in mapnames:
        inmap.load(w, mapname)

        runbsp.runBSP()
#       buildmap.buildMap()
#       writebsp.writeFile(mapname, "%s.wad" % mapname)
