import types
import collections

import wad
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


def recursiveBSP(objs):
    global vertexes
    global linedefs
    global sidedefs
    global sectors
    global b_nodes
    global b_leafs
    global b_numsplits

    print "%d VERTEXES" % len(objs["VERTEXES"])
    print "%d LINEDEFS" % len(objs["LINEDEFS"])
    print "%d SIDEDEFS" % len(objs["SIDEDEFS"])
    print "%d SECTORS" % len(objs["SECTORS"])

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

    _recursiveBSP(_createBLines())

    print "%d nodes" % len(b_nodes)
    print "%d leafs" % len(b_leafs)
    print "%d splits" % b_numsplits

########################################################################

SurfDesc = collections.namedtuple("SurfDesc", ["bline", "top", "bottom", "texture", "xoff", "yoff"])

o_planes = None
o_verts = None
o_edges = None
o_surfs = []
o_surfedges = []
o_nodes = []
o_leafs = []
o_verts_2d = None
o_lines_2d = None
o_leafs_2d = []


class Bounds(list):
    def __init__(self, *args, **kwargs):
        super(Bounds, self).__init__(*args, **kwargs)

        self.mins = [999999.0, 999999.0, 999999.0]
        self.maxs = [-999999.0, -999999.0, -999999.0]
        self.append(self.mins)
        self.append(self.maxs)

    def update(self, points):
        if type(points[0]) in [types.FloatType, types.IntType]:
            # a single point passed in
            points = [points]

        xyz = []
        xyz.append([p[0] for p in points])
        xyz.append([p[1] for p in points])
        xyz.append([p[2] for p in points])

        for i in xrange(3):
            self.mins[i] = min(self.mins[i], reduce(min, xyz[i]))
            self.maxs[i] = max(self.mins[i], reduce(max, xyz[i]))


class PlaneDump(object):
    """
    Note we don't go through any extra effort to find equal planes on
    any type of epsilon. Nearly coplanar planes will be counted as 2
    separate planes.
    """

    def __init__(self):
        self.planes = []
        self._p_to_index = {}

    def add(self, normal, dist):
        p = (normal[0], normal[1], normal[2], dist)
        mirror = (-normal[0], -normal[1], -normal[2], -dist)
        if mirror in self._p_to_index:
            return self._p_to_index[mirror] | 0x80000000
        elif p in self._p_to_index:
            return self._p_to_index[p]
        idx = len(self.planes)
        self._p_to_index[p] = idx
        self.planes.append(p)
        return idx


class VertexDump(object):
    """
    Note this can be used for 2d or 3d vertices.
    """

    def __init__(self):
        self.verts = []
        self._v_to_index = {}

    def add(self, v):
        if v in self._v_to_index:
            return self._v_to_index[v]
        idx = len(self.verts)
        self._v_to_index[v] = idx
        self.verts.append(v)
        return idx


class EdgeDump(object):
    """
    Note this can be used for 2d or 3d lines.
    """

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


def _line3DNormal(l):
    normal = (l.normal[0], 0.0, l.normal[1])
    dist = l.dist
    return (normal, dist)


def _genSurface(surfdesc):
#   xyz = []
#   xyz.append( (, , ) )
    # verts
    # edges
    # plane
    # plane side
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
            print "WARNING: one-sided line with upper texture"
            #TODO: print some more info so it can be tracked down
        if sidedef_front["bottomtexture"] != "-":
            print "WARNING: one-sided line with lower texture"
            #TODO: print some more info so it can be tracked down
        if sidedef_front["midtexture"] == "-":
            # hall-of-mirrors case
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
            if sidedef_front["toptexture"] == "-":
                print "WARNING: top surface with no texture"
                #TODO: print some more info so it can be tracked down

            ret.append( SurfDesc(bline,
                                 front_ceiling,
                                 back_ceiling,
                                 sidedef_front["toptexture"],
                                 sidedef_front["xoff"],
                                 sidedef_front["yoff"]) )

        # lower surface
        if back_floor > front_floor:
            if sidedef_front["bottomtexture"] == "-":
                print "WARNING: bottom surface with no texture"
                #TODO: print some more info so it can be tracked down

            ret.append( SurfDesc(bline,
                                 back_floor,
                                 front_floor,
                                 sidedef_front["bottomtexture"],
                                 sidedef_front["xoff"],
                                 sidedef_front["yoff"]) )

        # middle texture on a 2-sided line, secret wall or a grill texture
        if sidedef_front["midtexture"] != "-":
            ret.append( SurfDesc(bline,
                                 min(front_ceiling, back_ceiling),
                                 max(front_floor, back_floor),
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

    bbox = Bounds()
    for s in o_surfs[first_surf:]:
        #TODO: update bbox
        pass

    flags = 0x80000000

    ol = {}
    ol["flags"] = flags
    ol["bbox"] = bbox
    ol["firstsurface"] = first_surf
    ol["numsurfaces"] = num_surfs

    o_leafs.append(ol)


def _genNode(bnode):
    normal, dist = _line3DNormal(bnode["line"])

    flags = 0x0
    bbox = Bounds()
    front = bnode["front"]
    back = bnode["back"]
    plane = o_planes.add(normal, dist)

    on = {}
    on["flags"] = flags
    on["bbox"] = bbox
    on["front"] = front
    on["back"] = back
    on["plane"] = plane

    o_nodes.append(on)


def _recursiveUpdateOutputNodeBBox(onode):
    pass
    #TODO: ...


def _genLeaf2D(blines):
    first_line = len(o_lines_2d.edges)

    for bline in blines:
        v1 = o_verts_2d.add(bline.verts[0])
        v2 = o_verts_2d.add(bline.verts[1])

        o_lines_2d.add(v1, v2)

    num_lines = len(o_lines_2d.edges) - first_line

    leaf = {"firstline": first_line , "numlines": num_lines}
    o_leafs_2d.append(leaf)


def buildMap():
    global o_planes
    global o_verts
    global o_edges
    global o_surfs
    global o_surfedges
    global o_nodes
    global o_leafs
    global o_verts_2d
    global o_lines_2d
    global o_leafs_2d

    print ""
    print "Creating geometry..."

    o_planes = PlaneDump()
    o_verts = VertexDump()
    o_edges = EdgeDump()
    o_surfs = []
    o_surfedges = []
    o_nodes = []
    o_leafs = []
    o_verts_2d = VertexDump()
    o_lines_2d = EdgeDump()
    o_leafs_2d = []

    for blines in b_leafs:
        _genLeaf(blines)
        _genLeaf2D(blines)

    for bnode in b_nodes:
        _genNode(bnode)

    if o_nodes:
        _recursiveUpdateOutputNodeBBox(o_nodes[0])

    print "%d output planes" % len(o_planes.planes)
    print "%d output verts" % len(o_verts.verts)
    print "%d output edges" % len(o_edges.edges)
    print "%d output surfs" % len(o_surfs)
    print "%d output surfedges" % len(o_surfedges)
    print "%d output nodes" % len(o_nodes)
    print "%d output leafs" % len(o_leafs)
    print "%d output 2d verts" % len(o_verts_2d.verts)
    print "%d output 2d lines" % len(o_lines_2d.edges)
    print "%d output 2d leafs" % len(o_leafs_2d)

    ret = {}
    ret["planes"] = o_planes.planes
    ret["verts"] = o_verts.verts
    ret["edges"] = o_edges.edges
    ret["surfs"] = o_surfs
    ret["surfedges"] = o_surfedges
    ret["nodes"] = o_nodes
    ret["leafs"] = o_leafs
    ret["verts_2d"] = o_verts_2d.verts
    ret["lines_2d"] = o_lines_2d.edges
    ret["leafs_2d"] = o_leafs_2d

    return ret
