import collections

import line2d

#TODO: fix up t-junctions for 2-sided lines, where only one gets split

# original map objects from the WAD
vertexes = None
linedefs = None
sidedefs = None
sectors = None

# part of the BSP process
b_nodes = []
b_leafs = []
b_numsplits = 0


class BLine(line2d.Line2D):
    def __init__(self, linedef, is_backside=False):
        self.linedef = linedef

        # note that if we're on the back side we're using the linedef's
        # 2nd sidenum sidedef
        self.is_backside = is_backside

        v1 = (float(vertexes[linedef["v1"]][0]), float(vertexes[linedef["v1"]][1]))
        v2 = (float(vertexes[linedef["v2"]][0]), float(vertexes[linedef["v2"]][1]))

        if self.is_backside:
            v1, v2 = v2, v1

        super(BLine, self).__init__(v1, v2)


ChoiseParams = collections.namedtuple("ChoiseParams", ["index", "axial", "front", "back", "cross", "imbalance"])

#TODO: Probably check against a few different cutoffs; the idea is that
#      a lower cutoff (gives a better balanced tree) might be worth a
#      few extra splits.
IMBALANCE_CUTOFF = 0.5


def _chooseNodeLine(choiceparams):
    axial = filter(lambda cp: cp.axial, choiceparams)
    nonaxial = filter(lambda cp: not cp.axial, choiceparams)

    # sort the candidates by how well they divide the space; ideally
    # we would get a line that divides the space exactly in half with
    # the fewest splits
    by_imbalance_axial = sorted(axial, key=lambda cp: cp.imbalance)
    by_imbalance_nonaxial = sorted(nonaxial, key=lambda cp: cp.imbalance)

    best_axial = None
    for cp in by_imbalance_axial:
        if cp.imbalance > IMBALANCE_CUTOFF and best_axial is not None:
            break
        if best_axial is None:
            best_axial = cp
        elif cp.cross < best_axial.cross:
            best_axial = cp

    best_nonaxial = None
    for cp in by_imbalance_nonaxial:
        if cp.imbalance > IMBALANCE_CUTOFF and best_nonaxial is not None:
            break
        if best_nonaxial is None:
            best_nonaxial = cp
        elif cp.cross < best_nonaxial.cross:
            best_nonaxial = cp

    if best_axial:
        best = best_axial
    elif best_nonaxial:
        best = best_nonaxial
    else:
        # shouldn't happen
        raise Exception("no node chosen")

    return best


def _recursiveBSP(lines):
    global b_numsplits

    # find which lines can act as a partitioning node
    choiceparams = []
    for idx, l in enumerate(lines):
        front, back, cross = l.countSides(lines)
        if cross or (front and back):
            cp = ChoiseParams(idx, l.isAxial(), front, back, cross, abs(front - back) / float(len(lines)))
            choiceparams.append(cp)

    if not choiceparams:
        # no line splits the space into 2 parts; must be a leaf
        idx = len(b_leafs)
        b_leafs.append(lines)
        return idx | 0x80000000

    # find a good partitioning plane
    cp = _chooseNodeLine(choiceparams)
    nodeline = lines[cp.index]

    frontlines, backlines = nodeline.splitLines(lines)
    b_numsplits += len(frontlines) + len(backlines) - len(lines)

    if not frontlines:
        raise Exception("node chosen with no front space")
    if not backlines:
        raise Exception("node chosen with no back space")

    idx = len(b_nodes)
    b_nodes.append({})
    b_nodes[idx]["line"] = line2d.Line2D(nodeline.verts[0], nodeline.verts[1])
    b_nodes[idx]["front"] = _recursiveBSP(frontlines)
    b_nodes[idx]["back"] = _recursiveBSP(backlines)

    return idx


def _createBLines():
    lines = []

    for l in linedefs:
        sidenum0, sidenum1 = l["sidenum"]

        if sidenum0 < 0 or sidenum0 >= len(sidedefs):
            raise Exception("bad front sidedef %d" % sidenum0)
        lines.append(BLine(l))

        # create a line running in the opposite direction for 2-sided
        # linedefs
        if sidenum1 != -1:
            lines.append(BLine(l, is_backside=True))

    return lines


def runBSP(objs):
    global vertexes
    global linedefs
    global sidedefs
    global sectors
    global b_nodes
    global b_leafs
    global b_numsplits

    # negate each vertex y to match our coordinate system
    vertexes = [(x, -y) for x, y in objs["VERTEXES"]]
    linedefs = objs["LINEDEFS"]
    sidedefs = objs["SIDEDEFS"]
    sectors = objs["SECTORS"]

    b_nodes = []
    b_leafs = []
    b_numsplits = 0

    print ""
    print "Generating BSP tree..."

    blines = _createBLines()
    print "%d blines" % len(blines)

    _recursiveBSP(blines)

    print "%d nodes" % len(b_nodes)
    print "%d leafs" % len(b_leafs)
    print "%d splits" % b_numsplits

    ret = {}
    ret["nodes"] = b_nodes
    ret["leafs"] = b_leafs

    return ret
