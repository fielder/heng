import collections

import geom
import inmap

#TODO: fix up t-junctions for 2-sided lines, where only one gets split

# part of the BSP process
b_nodes = []
b_leafs = []
b_numsplits = 0
b_numon = 0
b_numlines = 0


class BLine(geom.Line2D):
    def __init__(self, linedef, is_backside=False):
        self.linedef = linedef

        # note that if we're on the back side we're using the linedef's
        # 2nd sidenum sidedef
        self.is_backside = is_backside

        v1 = (float(inmap.vertexes[linedef["v1"]][0]), float(inmap.vertexes[linedef["v1"]][1]))
        v2 = (float(inmap.vertexes[linedef["v2"]][0]), float(inmap.vertexes[linedef["v2"]][1]))

        if self.is_backside:
            v1, v2 = v2, v1

        super(BLine, self).__init__(v1, v2)


ChoiseParams = collections.namedtuple("ChoiseParams", ["index", "axial", "front", "back", "on", "cross", "imbalance"])

#TODO: Probably check against a few different cutoffs; the idea is that
#      a lower cutoff (gives a better balanced tree) might be worth a
#      few extra splits.
IMBALANCE_CUTOFF = 0.5


def _chooseNodeLine(choiceparams):
    # axial lines
    axial = filter(lambda cp: cp.axial, choiceparams)
    by_imbalance_axial = sorted(axial, key=lambda cp: cp.imbalance)

    best_axial = None
    for cp in by_imbalance_axial:
        if cp.imbalance > IMBALANCE_CUTOFF and best_axial is not None:
            break
        if best_axial is None:
            best_axial = cp
        elif cp.cross < best_axial.cross:
            best_axial = cp
    if best_axial:
        return best_axial

    # non-axial lines
    nonaxial = filter(lambda cp: not cp.axial, choiceparams)
    by_imbalance_nonaxial = sorted(nonaxial, key=lambda cp: cp.imbalance)

    best_nonaxial = None
    for cp in by_imbalance_nonaxial:
        if cp.imbalance > IMBALANCE_CUTOFF and best_nonaxial is not None:
            break
        if best_nonaxial is None:
            best_nonaxial = cp
        elif cp.cross < best_nonaxial.cross:
            best_nonaxial = cp
    if best_nonaxial:
        return best_nonaxial

    # shouldn't happen
    raise Exception("no node chosen")


def _recursiveBSP(lines, chopsurf):
    global b_numsplits
    global b_numon
    global b_numlines

    # find which lines can act as a partitioning node
    choiceparams = []
    for idx, l in enumerate(lines):
        front, back, cross, on = l.countSides(lines)
        if cross or (front and back):
            cp = ChoiseParams(idx, l.isAxial(), front, back, on, cross, abs(front - back) / float(len(lines)))
            choiceparams.append(cp)

    if not choiceparams:
        b_numlines += len(lines)

        # no line splits the space into 2 parts; must be a leaf
        idx = len(b_leafs)
        b_leafs.append(lines)
        return idx | 0x80000000

    # find a good partitioning plane
    cp = _chooseNodeLine(choiceparams)
    nodeline = geom.Line2D(lines[cp.index].verts[0], lines[cp.index].verts[1])

    # split lines
    frontlines, backlines, onlines = nodeline.splitLines(lines)
    b_numsplits += len(frontlines) + len(backlines) + len(onlines) - len(lines)
    b_numon += len(onlines)
    b_numlines += len(onlines)

    if not frontlines:
        raise Exception("node chosen with no front space")
    if not backlines:
        raise Exception("node chosen with no back space")

    # chop the chopsurf
    front_chop, back_chop = chopsurf.chopWithLine(nodeline)

    idx = len(b_nodes)
    b_nodes.append({})
    b_nodes[idx]["line"] = nodeline
    b_nodes[idx]["on"] = onlines
    b_nodes[idx]["front"] = _recursiveBSP(frontlines, front_chop)
    b_nodes[idx]["back"] = _recursiveBSP(backlines, back_chop)

    return idx


def _createBLines():
    lines = []

    for l in inmap.linedefs:
        sidenum0, sidenum1 = l["sidenum"]

        if sidenum0 < 0 or sidenum0 >= len(inmap.sidedefs):
            raise Exception("bad front sidedef %d" % sidenum0)
        lines.append(BLine(l))

        # create a line running in the opposite direction for 2-sided
        # linedef
        if sidenum1 != -1:
            lines.append(BLine(l, is_backside=True))

    return lines


def runBSP():
    global b_nodes
    global b_leafs
    global b_numsplits
    global b_numon
    global b_numlines

    b_nodes = []
    b_leafs = []
    b_numsplits = 0
    b_numon = 0
    b_numlines = 0

    print ""

    b = geom.Bounds2D()
    b.update(inmap.vertexes)
    b.update((b.mins[0] - 32.0, b.mins[1] - 32.0))
    b.update((b.maxs[0] + 32.0, b.maxs[1] + 32.0))
    chopsurf = geom.ChopSurface2D()
    chopsurf.setup(b.toPoints())

    blines = _createBLines()
    print "%d blines" % len(blines)
    print ""

    print "Generating BSP tree..."
    _recursiveBSP(blines, chopsurf)

    print "%d nodes" % len(b_nodes)
    print "%d leafs" % len(b_leafs)
    print "%d splits" % b_numsplits
    print "%d lines" % b_numlines
    print "%d lines on nodes" % b_numon
