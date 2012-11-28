import collections

import line2d

#TODO: fix up t-junctions for 2-sided lines, where only one gets split

# original map objects from the WAD
vertexes = []
linedefs = []
sidedefs = []
sectors = []

# part of the BSP process
b_nodes = []
b_leafs = []


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

    nodeline = line2d.Line2D(lines[cp.index].verts[0], lines[cp.index].verts[1])

    frontlines, backlines = nodeline.splitLines(lines)

    if not frontlines:
        raise Exception("node chosen with no front space")
    if not backlines:
        raise Exception("node chosen with no back space")

    idx = len(b_nodes)
    b_nodes.append({})
    b_nodes[idx]["node"] = nodeline
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


def recursiveBSP(objs):
    global vertexes
    global linedefs
    global sidedefs
    global sectors
    global b_nodes
    global b_leafs

    vertexes = objs["VERTEXES"]
    linedefs = objs["LINEDEFS"]
    sidedefs = objs["SIDEDEFS"]
    sectors = objs["SECTORS"]

    b_nodes = []
    b_leafs = []

    _recursiveBSP(_createBLines())

    print ""
    print "%d nodes" % len(b_nodes)
    print "%d leafs" % len(b_leafs)

########################################################################

class VertexDump(object):
    def __init__(self):
        self._verts = []
        self._v_to_idx = {}
    def add(self, v):
        if v in self._v_to_idx:
            return self._v_to_idx[v]
        self._v_to_idx[v] = len(self._verts)
        self._verts.append(v)

class EdgeDump(object):
    def __init__(self):
        self._edges = []
        self._e_to_idx = {}
    def add(self, v1, v2):
        e = (v1, v2)
        eb = (v2, v1)
        if eb in self._e_to_idx:
            return self._e_to_idx[eb] | 0x80000000
        elif e in self._e_to_idx:
            return self._e_to_idx[e]
        self._e_to_idx[e] = len(self._edges)
        self._edges.append(e)


SurfDesc = collections.namedtuple("SurfDesc", ["bline", "top", "bottom"])

o_planes = []
o_verts = []
o_edges = []
o_surfs = []
o_surfedges = []
o_nodes = []
o_leafs = []

#def _genPlane(plane): return the plane index, high bit set if on back side
#def _genVertex(v): return the vertex index
#def _genEdge(v1, v2): return the edge index, high bit set if runs backwards
#def _genSurface(surfdesc): emit a rectangular surface
#def _genLeaf(blines): emit planes/verts/edges/surfs/surfedges and the leaf; update bbox
#def _genNode(node): emit the node
#def _clearBBox():
#def _updateBBox(mins, maxs):
#def _planeForBLine(bline):


def buildMap():
    global o_planes
    global o_verts
    global o_edges
    global o_surfs
    global o_surfedges
    global o_nodes
    global o_leafs

    o_planes = []
    o_verts = []
    o_edges = []
    o_surfs = []
    o_surfedges = []
    o_nodes = []
    o_leafs = []

#   for idx, leaf in b_leafs:
#       surfs = []
#       for bline in leaf:
#           surfs.extend(_surfacesFromBLine(bline))
#       pass

#TODO: recursively update node bboxes
