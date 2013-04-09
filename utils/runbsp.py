import collections

import geom
import inmap

#TODO: fix up t-junctions for 2-sided lines, where only one gets split
#TODO: be sure to handle the case of 1 leaf and 0 nodes

vertexes_inv = []

# part of the BSP process
b_nodes = []
b_leafs = []
b_numsplits = 0
b_numon = 0
b_numlinestot = 0


class BLine(geom.Line2D):
    def __init__(self, linedef, is_backside=False):
        self.linedef = linedef

        # note that if we're on the back side we're using the linedef's
        # 2nd sidenum sidedef
        self.is_backside = is_backside

        v1 = (float(vertexes_inv[linedef["v1"]][0]), float(vertexes_inv[linedef["v1"]][1]))
        v2 = (float(vertexes_inv[linedef["v2"]][0]), float(vertexes_inv[linedef["v2"]][1]))

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
    global b_numlinestot

    choiceparams = []
    for idx, l in enumerate(lines):
        front, back, cross, on = l.countSides(lines)
        if cross or (front and back):
            choiceparams.append( ChoiseParams(idx, l.isAxial(),
                                              front, back, on, cross,
                                              abs(front - back) / float(len(lines))) )

    # no line splits the space into 2 parts; must be a leaf
    if not choiceparams:
        # leaf lines are done processing, add to total line tally
        b_numlinestot += len(lines)

        idx = len(b_leafs)
        b_leafs.append(lines)

#TODO: chop the surf w/ the remaining leaf lines & save off as the floor/ceiling polygon

        return idx | 0x80000000

    # must be a splitting node

    # find a good partitioning plane
    cp = _chooseNodeLine(choiceparams)
    nodeline = geom.Line2D(lines[cp.index].verts[0], lines[cp.index].verts[1])

    # split lines
    frontlines, backlines, onlines = nodeline.splitLines(lines)

    # no. times a split occurred is, (lines after splitting) - (lines before splitting)
    b_numsplits += len(frontlines) + len(backlines) + len(onlines) - len(lines)
    # how many lines are taken out of the bsp process because they lie
    # on a node; this is generally good as it helps reduce splits
    b_numon += len(onlines)
    # as the on-lines are taken out of the process, they're done and
    # won't be touched again
    b_numlinestot += len(onlines)

    if not frontlines:
        raise Exception("node chosen with no front space")
    if not backlines:
        raise Exception("node chosen with no back space")

    # chop the chopsurf
    front_chop, back_chop = geom.chopSurf(chopsurf, nodeline)
#   front_chop, back_chop = None, None

    idx = len(b_nodes)
    b_nodes.append({})
    b_nodes[idx]["cutter"] = nodeline
    b_nodes[idx]["on_lines"] = onlines
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

        # create a line running in the opposite direction for a 2-sided
        # linedef
        if sidenum1 != -1:
            lines.append(BLine(l, is_backside=True))

    return lines


def runBSP():
    global vertexes_inv
    global b_nodes
    global b_leafs
    global b_numsplits
    global b_numon
    global b_numlinestot

    b_nodes = []
    b_leafs = []
    b_numsplits = 0
    b_numon = 0
    b_numlinestot = 0

    print ""

    # negate each vertex y to match our coordinate system
    vertexes_inv = [(x, -y) for x, y in inmap.vertexes]

    b = geom.Bounds2D()
    b.update(vertexes_inv)
    b.update((b.mins[0] - 32.0, b.mins[1] - 32.0))
    b.update((b.maxs[0] + 32.0, b.maxs[1] + 32.0))
    chopsurf = geom.ChopSurface2D(verts=b.toPoints())

    blines = _createBLines()
    print "%d blines" % len(blines)
    print ""

    print "Generating BSP tree..."
    _recursiveBSP(blines, chopsurf)

    print "%d nodes" % len(b_nodes)
    print "%d leafs" % len(b_leafs)
    print "%d splits" % b_numsplits
    print "%d lines on nodes" % b_numon
    print "%d lines total" % b_numlinestot
