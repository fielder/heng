#!/usr/bin/env python

import sys

import wad
import inmap
import vec

#FIXME: initial node selection must account for 2-sided lines!!!

map_lines = []


def makeMapLines():
    global map_lines

    print ""

    map_lines = []
    for linedef in inmap.linedefs:
        x1, y1 = inmap.vertexes[linedef["v1"]]
        x2, y2 = inmap.vertexes[linedef["v2"]]

        # NOTE: We negate the y coordinates to match our right-handed
        # coordinate system.
        v1 = (x1, -y1)
        v2 = (x2, -y2)

        line = vec.Line2D(v1, v2)
        line.linedef = linedef

        map_lines.append(line)

    print "%d lines" % len(map_lines)


class NodeChoice(object):
    line = None
    axial = False
    front = None
    back = None
    cross = None
    on = None
    imbalance = 0.0


def _chooseNode(choices):
    axial = filter(lambda c: c.axial, choices)
    nonaxial = filter(lambda c: not c.axial, choices)

    for by_axis_list in (axial, nonaxial):
        best = None
        for c in sorted(by_axis_list, key=lambda x: x.imbalance):
            if c.imbalance > 0.5 and best is not None:
                # don't choose a node with wildly imbalanced children
                break
            if best is None:
                best = c
            elif c.cross < best.cross:
                best = c
        if best:
            return best

    # shouldn't happen
    raise Exception("no node chosen")


def _getNodeChoices(lines):
    choices = []
    for l in lines:
        front, back, cross, on = l.countLinesSides(lines)

        if cross or (front and back):
            nc = NodeChoice()
            nc.line = l
            nc.axial = l.axial
            nc.front = front
            nc.back = back
            nc.cross = cross
            nc.on = on
            nc.imbalance = abs(nc.front - nc.back) / float(len(lines))

            choices.append(nc)
    return choices


def _recursiveFindNodes(lines):
    choices = _getNodeChoices(lines)

    if not choices:
        # no node found, the lines form a leaf
        return None

    chosen = _chooseNode(choices)

    front, back, on = chosen.line.splitLines(lines)

    ret = vec.Line2D(chosen.line)
    ret.back = _recursiveFindNodes(back)
    ret.front = _recursiveFindNodes(front)
    return ret


stats = {}
def _nodesStats(node, depth=0):
    stats["depth"] = max(stats["depth"], depth)
    if not node:
        stats["leafs"] += 1
    else:
        stats["nodes"] += 1
        if node.axial:
            stats["axial"] += 1
        else:
            stats["nonaxial"] += 1
        _nodesStats(node.back, depth + 1)
        _nodesStats(node.front, depth + 1)


def genNodes():
    print ""
    print "Finding BSP nodes..."

    head = _recursiveFindNodes(map_lines)

    stats["nodes"] = 0
    stats["leafs"] = 0
    stats["axial"] = 0
    stats["nonaxial"] = 0
    stats["depth"] = 0
    _nodesStats(head)
    print "%d nodes" % stats["nodes"]
    print "%d leafs" % stats["leafs"]
    print "%d axial" % stats["axial"]
    print "%d non-axial" % stats["nonaxial"]
    print "%d max depth" % stats["depth"]

    return head


def makeChopsurf():
    x_coords = []
    for l in map_lines:
        x_coords.append(l[0].x)
        x_coords.append(l[1].x)
    y_coords = []
    for l in map_lines:
        y_coords.append(l[0].y)
        y_coords.append(l[1].y)

    min_x = min(x_coords)
    min_y = min(y_coords)
    max_x = max(x_coords)
    max_y = max(y_coords)

    v1 = (min_x, min_y)
    v2 = (min_x, max_y)
    v3 = (max_x, max_y)
    v4 = (max_x, min_y)

    return vec.Poly2D([v1, v2, v3, v4])


def _blinesFromMapLine(l):
    ret = []

    def _add(v1, v2, top, bot):
        bl = vec.Line2D(v1, v2)
        bl.top = top
        bl.bottom = bot
        ret.append(bl)

    sidenum_front = l.linedef["sidenum"][0]
    sidenum_back = l.linedef["sidenum"][1]

    sidedef_front = inmap.sidedefs[sidenum_front]
    sector_front = inmap.sectors[sidedef_front["sector"]]
    floor_front = sector_front["floorheight"]
    ceil_front = sector_front["ceilingheight"]

    if sidenum_back == -1:
        if floor_front < ceil_front:
            _add(l[0], l[1], ceil_front, floor_front)
    else:
        sidedef_back = inmap.sidedefs[sidenum_back]
        sector_back = inmap.sectors[sidedef_back["sector"]]
        floor_back = sector_back["floorheight"]
        ceil_back = sector_back["ceilingheight"]

        if floor_back > floor_front:
            # a step up going from font sector to back
            _add(l[0], l[1], floor_back, floor_front)
        elif floor_back < floor_front:
            # a step down going from font sector to back
            _add(l[1], l[0], floor_front, floor_back)

        if ceil_back < ceil_front:
            # watch your head
            _add(l[0], l[1], ceil_front, ceil_back)
        elif ceil_back > ceil_front:
            # more head room
            _add(l[1], l[0], ceil_back, ceil_front)

        #TODO: "secret" 2-sided walls with a middle texture

    return ret


def makeBLines():
    ret = []

    for l in map_lines:
        ret.extend(_blinesFromMapLine(l))

    print ""
    print "%d blines" % len(ret)

    return ret


def _splitBLine(splitter, bline):
    f, b, o = splitter.splitLine(bline)

    # the bline is colinear with the splitter, determine the side by
    # looking at the normal
    if o:
        p = bline.normal * bline.dist + (bline.normal * 10.0)
        side = splitter.pointSide(p)
        if side == vec.SIDE_FRONT:
            f = o
        elif side == vec.SIDE_BACK:
            b = o
        else:
            raise Exception("could not determine line (%s) side of splitter (%s)" % (repr(bline), repr(splitter)))

    # preserve the top/bottom parts of the polygon
    if f:
        f.top = bline.top
        f.bottom = bline.bottom
    if b:
        b.top = bline.top
        b.bottom = bline.bottom

    return (f, b)


def _chopBLines(node, blines):
    front = []
    back = []

    for bl in blines:
        f, b = _splitBLine(node, bl)
        if f:
            front.append(f)
        if b:
            back.append(b)

    return (front, back)


def _polysForLeaf(blines, chopsurf):
    polys = []

    print ""
    for bl in blines:
        print bl,bl.top,bl.bottom
    #TODO: ensure each bline faces each other
    #TODO: chop the chopsurf with the blines
    #TODO: make 3d polys for blines, floor, and ceiling

    return polys


def _recursiveBSP(node, blines, chopsurf):
    if node is None:
        # is a leaf
        return _polysForLeaf(blines, chopsurf)

    blines_front, blines_back = _chopBLines(node, blines)

    chop_front, chop_back = chopsurf.splitWithLine(node)

    back = _recursiveBSP(node.back, blines_back, chop_back)
    front = _recursiveBSP(node.front, blines_front, chop_front)

    return back + front


def genPolys(head, blines, chopsurf):
    ret = _recursiveBSP(head, blines, chopsurf)

    print ""
    print "%d polys" % len(ret)

    return ret


def writePolys(path, polys):
    print ""
    print "Writing \"%s\" ..." % path

#   fp = open(path, "wt")

    #...
    #...

#   fp.close()


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

        makeMapLines()
        head = genNodes()
        chopsurf = makeChopsurf()
        blines = makeBLines()
        polys = genPolys(head, blines, chopsurf)

        outpath = "%s.polys" % mapname
        writePolys(outpath, polys)
