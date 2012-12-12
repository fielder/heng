#TODO: check for degenerate faces
#TODO: make sure all surfaces on a node reference *exactly* that node's plane

import types
import collections

import inmap
import runbsp

SurfDesc = collections.namedtuple("SurfDesc", ["bline", "top", "bottom", "texture", "xoff", "yoff"])

o_planes = None
o_verts = None
o_edges = None
o_sectors = []
o_faces = []
o_surfaces = []
o_surfedges = []
o_nodes = []
o_leafs = []
o_verts_2d = None
o_lines_2d = None
o_leafs_2d = []


class Bounds(object):
    def __init__(self):
        self.mins = [999999.0, 999999.0, 999999.0]
        self.maxs = [-999999.0, -999999.0, -999999.0]

    def __repr__(self):
        return repr((self.mins, self.maxs))

    def __getitem__(self, i):
        return (self.mins, self.maxs)[i]

    def update(self, other):
        if isinstance(other, Bounds):
            # other bounds
            for i in xrange(3):
                self.mins[i] = min(self.mins[i], other.mins[i])
                self.maxs[i] = max(self.maxs[i], other.maxs[i])
            return

        if isinstance(other[0], float) or isinstance(other[0], int):
            # single point
            points = [other]
        else:
            # list/tuple of points
            points = other

        for i in xrange(3):
            vals = [p[i] for p in points]
            self.mins[i] = float(min(self.mins[i], min(vals)))
            self.maxs[i] = float(max(self.maxs[i], max(vals)))


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
    normal, dist = _line3DNormal(surfdesc.bline)
    planenum = o_planes.add(normal, dist)

    vert_xyz = []
    vert_xyz.append( (surfdesc.bline.verts[0][0], surfdesc.top,    surfdesc.bline.verts[0][1]) )
    vert_xyz.append( (surfdesc.bline.verts[0][0], surfdesc.bottom, surfdesc.bline.verts[0][1]) )
    vert_xyz.append( (surfdesc.bline.verts[1][0], surfdesc.bottom, surfdesc.bline.verts[1][1]) )
    vert_xyz.append( (surfdesc.bline.verts[1][0], surfdesc.top,    surfdesc.bline.verts[1][1]) )
    verts_idx = [o_verts.add(p) for p in vert_xyz]
    verts_idx.append(verts_idx[0]) # wrap-around case

    edges = [o_edges.add(v1, v2) for v1, v2 in zip(verts_idx, verts_idx[1:])]

    first_surfedge = len(o_surfedges)
    o_surfedges.extend(edges)
    num_surfedges = len(edges)

    bbox = Bounds()
    print vert_xyz
    for xyz in vert_xyz:
        bbox.update(xyz)
    print bbox

    s = {}
    s["planenum"] = planenum
    s["firstedge"] = first_surfedge
    s["numedges"] = num_surfedges
    s["bbox"] = bbox

    o_surfaces.append(s)


def _lineSurfDesc(bline):
    if bline.is_backside:
        sidenum_front = bline.linedef["sidenum"][1]
        sidenum_back = bline.linedef["sidenum"][0]
    else:
        sidenum_front = bline.linedef["sidenum"][0]
        sidenum_back = bline.linedef["sidenum"][1]

    sidedef_front = inmap.sidedefs[sidenum_front]
    if sidenum_back != -1:
        sidedef_back = inmap.sidedefs[sidenum_back]
    else:
        sidedef_back = None

    front_sector = inmap.sectors[sidedef_front["sector"]]
    if sidedef_back is not None:
        back_sector = inmap.sectors[sidedef_back["sector"]]
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

#FIXME: It's possible to have a leaf with no surfaces, caused by the
#       lines in the leaf to be simple 2-sided passable lines.
#       This should stop happening when solid floors/ceilings are added.

def _genLeaf(blines):
    first_surf = len(o_surfaces)
    for bline in blines:
        for surfdesc in _lineSurfDesc(bline):
            _genSurface(surfdesc)
    num_surfs = len(o_surfaces) - first_surf

    bbox = Bounds()
    for s in o_surfaces[first_surf:]:
        bbox.update(s["bbox"])

    ol = {}
    ol["flags"] = 0x80000000
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


# verts
# planes
# edges
# sectors
# faces
# surfaces
# leafs
# nodes
# surf edges

# portals

def buildMap():
    global o_planes
    global o_verts
    global o_edges
    global o_sectors
    global o_faces
    global o_surfaces
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
    o_sectors = []
    o_faces = []
    o_surfaces = []
    o_surfedges = []
    o_nodes = []
    o_leafs = []
    o_verts_2d = VertexDump()
    o_lines_2d = EdgeDump()
    o_leafs_2d = []

    for blines in runbsp.b_leafs:
        _genLeaf(blines)

#   for blines in objs["leafs"]:
#       _genLeaf2D(blines)

#   for bnode in objs["nodes"]:
#       _genNode(bnode)

#   if o_nodes:
#       _recursiveUpdateOutputNodeBBox(o_nodes[0])

    print "%d planes" % len(o_planes.planes)
    print "%d verts" % len(o_verts.verts)
    print "%d edges" % len(o_edges.edges)
    print "%d sectors" % len(o_sectors)
    print "%d faces" % len(o_faces)
    print "%d surfs" % len(o_surfaces)
    print "%d surfedges" % len(o_surfedges)
    print "%d nodes" % len(o_nodes)
    print "%d leafs" % len(o_leafs)
    print "%d 2d verts" % len(o_verts_2d.verts)
    print "%d 2d lines" % len(o_lines_2d.edges)
    print "%d 2d leafs" % len(o_leafs_2d)

    ret = {}
    ret["planes"] = o_planes.planes
    ret["vertexes"] = o_verts.verts
    ret["edges"] = o_edges.edges
    ret["sectors"] = o_sectors
    ret["faces"] = o_faces
    ret["surfaces"] = o_surfaces
    ret["surfedges"] = o_surfedges
    ret["nodes"] = o_nodes
    ret["leafs"] = o_leafs
    ret["verts_2d"] = o_verts_2d.verts
    ret["lines_2d"] = o_lines_2d.edges
    ret["leafs_2d"] = o_leafs_2d

    return ret
