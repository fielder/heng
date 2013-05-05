#!/usr/bin/env python

import sys

import wad
import inmap
import vec


def _genPoly(bottom, top, v1, v2):
    p = vec.Poly()

    p.verts.append(vec.Vec(v1[0], bottom, v1[1]))
    p.verts.append(vec.Vec(v2[0], bottom, v2[1]))
    p.verts.append(vec.Vec(v2[0], top,    v2[1]))
    p.verts.append(vec.Vec(v1[0], top,    v1[1]))

    return p


def _genPolys():
    ret = []

    for l in inmap.linedefs:
        v1 = inmap.vertexes[l["v1"]]
        v2 = inmap.vertexes[l["v2"]]

        sidenum_front = l["sidenum"][0]
        sidenum_back = l["sidenum"][1]

        sidedef_front = inmap.sidedefs[sidenum_front]
        sector_front = inmap.sectors[sidedef_front["sector"]]
        floor_front = sector_front["floorheight"]
        ceil_front = sector_front["ceilingheight"]

        if sidenum_back == -1:
            ret.append(_genPoly(floor_front, ceil_front, v1, v2))
        else:
            sidedef_back = inmap.sidedefs[sidenum_back]
            sector_back = inmap.sectors[sidedef_back["sector"]]
            floor_back = sector_back["floorheight"]
            ceil_back = sector_back["ceilingheight"]

            if floor_back > floor_front:
                # a step up going from font sector to back
                ret.append(_genPoly(floor_front, floor_back, v1, v2))
            elif floor_back < floor_front:
                # a step down going from font sector to back
                ret.append(_genPoly(floor_back, floor_front, v2, v1))

            if ceil_back < ceil_front:
                # watch your head
                ret.append(_genPoly(ceil_back, ceil_front, v1, v2))
            elif ceil_back > ceil_front:
                # more head room
                ret.append(_genPoly(ceil_front, ceil_back, v2, v1))

            #TODO: "secret" 2-sided walls with a middle texture

    return ret


def _writePolys(path, polys):
    print ""
    print "Writing \"%s\" ..." % path

    fp = open(path, "wt")
    for p in polys:
        fp.write("%s\n" % str(p))
    fp.close()


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

        _writePolys("%s.polys" % mapname, _genPolys())
