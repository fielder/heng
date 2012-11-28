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
    nodeline = lines[cp.index]

    frontlines, backlines = nodeline.splitLines(lines)

    if not frontlines:
        raise Exception("node chosen with no front space")
    if not backlines:
        raise Exception("node chosen with no back space")

    idx = len(b_nodes)
    b_nodes.append({})
    b_nodes[idx]["node"] = line2d.Line2D(nodeline.verts[0], nodeline.verts[1])
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

class PlaneDump(object):
    def __init__(self):
        self.planes = []
        #TODO: ...

    def add(self, p):
        pass
        #TODO: use back-facing planes
        #TODO: ...


class VertexDump(object):
    def __init__(self):
        self.verts = []
        self._v_to_index = {}

    def add(self, xyz):
        if xyz in self._v_to_index:
            return self._v_to_index[xyz]
        idx = len(self.verts)
        self._v_to_index[xyz] = idx
        self.verts.append(xyz)
        return idx


class EdgeDump(object):
    def __init__(self):
        self.edges = []
        self._e_to_index = {}

    def add(self, v1_idx, v2_idx):
        e = (v1_idx, v2_idx)
        eb = (v2_idx, v1_idx)
        if eb in self._e_to_index:
            return self._e_to_index[eb] | 0x80000000
        elif e in self._e_to_index:
            return self._e_to_index[e]
        idx = len(self.edges)
        self._e_to_index[e] = idx
        self.edges.append(e)
        return idx


SurfDesc = collections.namedtuple("SurfDesc", ["bline", "top", "bottom", "texture", "xoff", "yoff"])
Bounds = collections.namedtuple("Bounds", ["mins", "maxs"])

o_planes = None
o_verts = None
o_edges = None
o_surfs = []
o_surfedges = []
o_nodes = []
o_leafs = []


def _clearBounds():
    return Bounds((999999.0, 999999.0, 999999.0), (-999999.0, -999999.0, -999999.0))


def _updateBounds(bounds, p):
    mins, maxs = bounds
    mins = (min(mins[0], p[0]), min(mins[1], p[1]), min(mins[2], p[2]))
    maxs = (max(maxs[0], p[0]), max(maxs[1], p[1]), max(maxs[2], p[2]))
    return Bounds(mins, maxs)


def _planeForBLine(bline):
    normal = (bline.normal[0], 0.0, bline.normal[1])
    dist = bline.dist
    return (normal, dist)


def _genPlane(plane):
    pass


def _genSurface(surfdesc):
    #TODO: emit a rectangular surface
    pass


def _lineSurfDescs(bline):
    if bline.is_backside:
        sidenum_front = bline.linedef["sidenum"][1]
        sidenum_back = bline.linedef["sidenum"][0]
    else:
        sidenum_front = bline.linedef["sidenum"][0]
        sidenum_back = bline.linedef["sidenum"][1]

    sidedef_front = sidedefs[sidenum_front]
    if sidenum_back != -1:
        sidedef_back = sidedefs[sidenum_back]
    else:
        sidedef_back = None

    front_sector = sectors[sidedef_front["sector"]]
    if sidedef_back is not None:
        back_sector = sectors[sidedef_back["sector"]]
    else:
        back_sector = None

    ret = []

    front_ceiling = front_sector["ceilingheight"]
    front_floor = front_sector["floorheight"]

    if not back_sector:
        if sidedef_front["toptexture"] != "-":
            raise Exception("one-sided line with upper texture")
        if sidedef_front["bottomtexture"] != "-":
            raise Exception("one-sided line with lower texture")
        if sidedef_front["midtexture"] == "-":
            raise Exception("one-sided line without middle texture")

        ret.append( SurfDesc(bline,
                             front_ceiling,
                             front_floor,
                             sidedef_front["midtexture"],
                             sidedef_front["xoff"],
                             sidedef_front["yoff"]) )
    else:
        back_ceiling = back_sector["ceilingheight"]
        back_floor = back_sector["floorheight"]

        # upper surface
        if back_ceiling < front_ceiling:
            ret.append( SurfDesc(bline,
                                 front_ceiling,
                                 back_ceiling,
                                 sidedef_front["toptexture"],
                                 sidedef_front["xoff"],
                                 sidedef_front["yoff"]) )

        # lower surface
        if back_floor > front_floor:
            ret.append( SurfDesc(bline,
                                 back_floor,
                                 front_floor,
                                 sidedef_front["bottomtexture"],
                                 sidedef_front["xoff"],
                                 sidedef_front["yoff"]) )

        # middle texture on a 2-sided line, secret wall or a grill texture
        if sidedef_front["midtexture"] != "-":
            ret.append( SurfDesc(bline,
                                 front_ceiling,
                                 front_floor,
                                 sidedef_front["midtexture"],
                                 sidedef_front["xoff"],
                                 sidedef_front["yoff"]) )

    return ret


def _genLeaf(blines):
    first_surf = len(o_surfs)

    for bline in blines:
        for surfdesc in _lineSurfDescs(bline):
            _genSurface(surfdesc)

    num_surfs = len(o_surfs) - first_surf

    #TODO: flags
    #TODO: bbox
    #TODO: first surf
    #TODO: num surfs


def _genNode(bnode):
    pass
    #TODO: flags
    #TODO: bbox
    #TODO: plane
    #TODO: children


def buildMap():
    global o_planes
    global o_verts
    global o_edges
    global o_surfs
    global o_surfedges
    global o_nodes
    global o_leafs

    o_planes = PlaneDump()
    o_verts = VertexDump()
    o_edges = EdgeDump()
    o_surfs = []
    o_surfedges = []
    o_nodes = []
    o_leafs = []

    for blines in b_leafs:
        _genLeaf(blines)

    for bnode in b_nodes:
        _genNode(bnode)

#TODO: recursively update node bboxes
