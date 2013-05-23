#!/usr/bin/env python

import sys

import wad
import inmap
import vec


def _getVertex(wad_vertex_idx):
    # We negate the y to match our right-handed coordinate system.
    x, y = inmap.vertexes[wad_vertex_idx]
    return vec.Vec2(x, -y)


class BLine(vec.Line2D):
    def __init__(self, linedef, is_front_side):
        self.linedef = linedef
        self.sidedef = None
        self.sidedef_back = None

        sidenum_front = linedef["sidenum"][0]
        sidenum_back = linedef["sidenum"][1]

        # Note that to keep the normals pointing in the correct
        # direction we reverse the vertex ordering.
        if is_front_side:
            v1 = _getVertex(linedef["v2"])
            v2 = _getVertex(linedef["v1"])
            self.sidedef = inmap.sidedefs[sidenum_front]

            if sidenum_back != -1:
                self.sidedef_back = inmap.sidedefs[sidenum_back]
        else:
            v1 = _getVertex(linedef["v1"])
            v2 = _getVertex(linedef["v2"])
            self.sidedef = inmap.sidedefs[sidenum_back]

            if sidenum_front != -1:
                self.sidedef_back = inmap.sidedefs[sidenum_front]

        super(BLine, self).__init__(v1, v2)


def _blinesFromLinedef(linedef):
    ret = []

    ret.append(BLine(linedef, True))

    if linedef["sidenum"][1] != -1:
        ret.append(BLine(linedef, False))

    return ret


def makeBLines():
    ret = []

    for linedef in inmap.linedefs:
        ret.extend(_blinesFromLinedef(linedef))

    print ""
    print "%d blines" % len(ret)

    return ret


class BSPLeaf(object):
    def __init__(self):
        self.blines = []
        self.chopsurf = None


class BSPNode(object):
    def __init__(self):
        self.line = None
        self.front = None
        self.back = None


class NodeChoice(object):
    bline = None
    front = None
    back = None
    cross = None
    imbalance = 0.0


IMBALANCE_CUTOFF = 0.5

def _chooseNodeLine(choices):
    axial = filter(lambda c: c.bline.axial, choices)
    nonaxial = filter(lambda c: not c.bline.axial, choices)

    for by_axis_list in (axial, nonaxial):
        best = None
        for c in sorted(by_axis_list, key=lambda x: x.imbalance):
            if c.imbalance > IMBALANCE_CUTOFF and best is not None:
                # don't choose a node with wildly imbalanced children
                break
            if best is None:
                best = c
            elif c.cross < best.cross:
                best = c
        if best:
            return vec.Line2D(best.bline)

    # shouldn't happen
    raise Exception("no node chosen")


def _getNodeChoices(blines):
    choices = []
    for bl in blines:
        front, back, cross, on = bl.countLinesSides(blines, include_on=False)
        if on:
            raise Exception("on lines when not requested")

        if cross or (front and back):
            nc = NodeChoice()
            nc.bline = bl
            nc.front = front
            nc.back = back
            nc.cross = cross
            nc.imbalance = abs(nc.front - nc.back) / float(len(blines))

            choices.append(nc)
    return choices


def _splitLines(line, blines):
    front = []
    back = []

    for bl in blines:
        f, b, o = line.splitLine(bl, include_on=False)
        if o:
            raise Exception("on lines when not requested")

        # can't lose the extras we tacked onto the blines
        if f:
            f.linedef = bl.linedef
            f.sidedef = bl.sidedef
            f.sidedef_back = bl.sidedef_back
            front.append(f)
        if b:
            b.linedef = bl.linedef
            b.sidedef = bl.sidedef
            b.sidedef_back = bl.sidedef_back
            back.append(b)

    return (front, back)


def _recursiveBSP(blines, chopsurf):
    choices = _getNodeChoices(blines)

    if not choices:
        # no node found, the lines form a leaf

        for bl in blines:
            chopsurf, toss = chopsurf.splitWithLine(bl)

        ret = BSPLeaf()
        ret.blines = blines
        ret.chopsurf = chopsurf
    else:
        nodeline = _chooseNodeLine(choices)

        front, back = _splitLines(nodeline, blines)

        chop_front, chop_back = chopsurf.splitWithLine(nodeline)

        ret = BSPNode()
        ret.line = nodeline
        ret.front = _recursiveBSP(front, chop_front)
        ret.back = _recursiveBSP(back, chop_back)

    return ret


stats = {}
def _nodesStats(node, depth=0):
    stats["depth"] = max(stats["depth"], depth)
    if isinstance(node, BSPLeaf):
        stats["leafs"] += 1
    else:
        stats["nodes"] += 1
        if node.line.axial:
            stats["axial"] += 1
        else:
            stats["nonaxial"] += 1
        _nodesStats(node.back, depth + 1)
        _nodesStats(node.front, depth + 1)


def runBSP(blines, chopsurf):
    print ""
    print "Recursive BSP..."

    head = _recursiveBSP(blines, chopsurf)

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


def makeChopsurf(blines):
    x_coords = []
    for bl in blines:
        x_coords.append(bl[0][0])
        x_coords.append(bl[1][0])
    y_coords = []
    for bl in blines:
        y_coords.append(bl[0][1])
        y_coords.append(bl[1][1])

    min_x = min(x_coords)
    min_y = min(y_coords)
    max_x = max(x_coords)
    max_y = max(y_coords)

    v1 = (min_x, min_y)
    v2 = (min_x, max_y)
    v3 = (max_x, max_y)
    v4 = (max_x, min_y)

    return vec.Poly2D([v1, v2, v3, v4])


def _makeWallQuad(v1, v2, low, high):
    ret = vec.Poly3D()

    ret.append((v1[0], low, v1[1]))
    ret.append((v1[0], high, v1[1]))
    ret.append((v2[0], high, v2[1]))
    ret.append((v2[0], low, v2[1]))

    return ret


def _polysForBLine(bl):
    ret = []

    sector_front = inmap.sectors[bl.sidedef["sector"]]
    floor_front = sector_front["floorheight"]
    ceil_front = sector_front["ceilingheight"]

    if not bl.sidedef_back:
        if floor_front < ceil_front:
            ret.append(_makeWallQuad(bl[0], bl[1], floor_front, ceil_front))
    if bl.sidedef_back:
        sector_back = inmap.sectors[bl.sidedef_back["sector"]]
        floor_back = sector_back["floorheight"]
        ceil_back = sector_back["ceilingheight"]

        if floor_back > floor_front:
            ret.append(_makeWallQuad(bl[0], bl[1], floor_front, floor_back))
        if ceil_back < ceil_front:
            ret.append(_makeWallQuad(bl[0], bl[1], ceil_back, ceil_front))

    return ret


def _polysForLeaf(leaf):
    ret = []

    # walls
    for bl in leaf.blines:
        ret.extend(_polysForBLine(bl))

    # floor & ceiling
    bl = leaf.blines[0]
    floorheight = inmap.sectors[bl.sidedef["sector"]]["floorheight"]
    ceilingheight = inmap.sectors[bl.sidedef["sector"]]["ceilingheight"]

    floor = vec.Poly3D()
    for v in leaf.chopsurf:
        floor.append((v[0], floorheight, v[1]))
    ret.append(floor)

    ceil = vec.Poly3D()
    for v in reversed(leaf.chopsurf):
        ceil.append((v[0], ceilingheight, v[1]))
    ret.append(ceil)

    return ret


def _recursiveGenPolys(node):
    ret = []

    if isinstance(node, BSPLeaf):
        ret.extend(_polysForLeaf(node))
    else:
        ret.extend(_recursiveGenPolys(node.back))
        ret.extend(_recursiveGenPolys(node.front))

    return ret


def genPolys(head):
    ret = _recursiveGenPolys(head)

    print ""
    print "%d polys" % len(ret)

    return ret


def writePolys(path, polys):
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

        blines = makeBLines()
        chopsurf = makeChopsurf(blines)
        head = runBSP(blines, chopsurf)
        polys = genPolys(head)

        outpath = "%s.polys" % mapname
        writePolys(outpath, polys)
