import math
import copy
import collections

#TODO: fix up t-junctions for 2-sided lines, where only one gets split
#TODO: print some counters
#     - avg imbalance
#     - best imbalance, worst imbalance
#     - num splits
#     - average node splits
#     - best splits, worst splits
#     - num axial nodes, num non-axial

# original map objects from the WAD
vertexes = []
linedefs = []
sidedefs = []
sectors = []

# part of the BSP process
b_nodes = []
b_leafs = []

# output objects
o_verts = []

SIDE_EPSILON = 0.02

SIDE_ON    = 0 # lies on the line
SIDE_FRONT = 1
SIDE_BACK  = 2
SIDE_CROSS = 3


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


class Line(object):
    def __init__(self, v1, v2):
        self.verts = (v1, v2)

        dx, dy = self.delta()
        normal = (dy, -dx)
        len_ = math.hypot(*normal)
        self.normal = (normal[0] / len_, normal[1] / len_)
        self.dist = dot(self.verts[0], self.normal)

    def delta(self):
        return (self.verts[1][0] - self.verts[0][0], self.verts[1][1] - self.verts[0][1])

    def isAxial(self):
        return math.fabs(self.normal[0]) == 1.0 or math.fabs(self.normal[1]) == 1.0

    def pointSide(self, p):
        d = dot(self.normal, p) - self.dist

        if math.fabs(d) < SIDE_EPSILON:
            side = SIDE_ON
        elif d < 0:
            side = SIDE_BACK
        elif d > 0:
            side = SIDE_FRONT
        else:
            raise Exception("shouldn't happen")

        return side

    def pointsSides(self, points):
        return [self.pointSide(p) for p in points]

    def lineSide(self, other):
        """
        Find which side other lies on. Note if the other line is
        colinear, we use the other's normal to determine whether
        it's on our front or back side.
        """

        s1, s2 = self.pointsSides( (other.verts[0], other.verts[1]) )

        if s1 == s2:
            if s1 == SIDE_ON:
                x = other.verts[0][0] + other.normal[0] * 8.0
                y = other.verts[0][1] + other.normal[1] * 8.0
                side = self.pointSide((x, y))
            else:
                # both on one side
                side = s1
        elif s1 == SIDE_ON:
            side = s2
        elif s2 == SIDE_ON:
            side = s1
        else:
            side = SIDE_CROSS

        if side == SIDE_ON:
            # shouldn't happen
            raise Exception("lineSide() gave ON")

        return side

#TODO: get rid of this func, just put the line where it's called
    def _updateV1(self, v):
        """
        Note it's assumed the new vertex is colinear with the old line.
        We don't update our normal.
        """

        self.verts = (v, self.verts[1])

#TODO: get rid of this func, just put the line where it's called
    def _updateV2(self, v):
        """
        Note it's assumed the new vertex is colinear with the old line.
        We don't update our normal.
        """

        self.verts = (self.verts[0], v)

    def _splitCrossingLine(self, other):
        """
        It's assumed other is known to cross.
        """

        d1 = dot(self.normal, other.verts[0]) - self.dist
        d2 = dot(self.normal, other.verts[1]) - self.dist

        frac = d1 / (d1 - d2)
        mid_x = self.verts[0][0] + frac * (self.verts[1][0] - self.verts[0][0]);
        mid_y = self.verts[0][1] + frac * (self.verts[1][1] - self.verts[0][1]);
        mid = (mid_x, mid_y)

        front = copy.copy(self)
        back = copy.copy(self)

        if d1 < 0:
            back._updateV2(mid)
            front._updateV1(mid)
        else:
            back._updateV1(mid)
            front._updateV2(mid)

        return (front, back)

    def splitLine(self, other):
        side = self.lineSide(other)

        if side == SIDE_FRONT:
            front = other
            back = None
        elif side == SIDE_BACK:
            front = None
            back = other
        else:
            front, back = self._splitCrossingLine(other)

        return (front, back)

    def splitLines(self, lines):
        front = []
        back = []
        for l in lines:
            f, b = self.splitLine(l)
            if f:
                front.append(f)
            if b:
                back.append(b)
        return (front, back)


class BLine(Line):
    def __init__(self, linedef, is_backside=False):
        self.linedef = linedef
        self.is_backside = is_backside

        v1 = (float(vertexes[linedef["v1"]][0]), float(vertexes[linedef["v1"]][1]))
        v2 = (float(vertexes[linedef["v2"]][0]), float(vertexes[linedef["v2"]][1]))

        if self.is_backside:
            v1, v2 = v2, v1

        super(BLine, self).__init__(v1, v2)


#FIXME: Will fail for cases where all lines are colinear, but lines
#       lie on both sides of one. Is this case even possible?
def _isConvex(lines):
    """
    Check if a set of lines form a convex space. If 2 separate vertices
    lay on opposite sides of a line, it's non-convex.
    """

    for l in lines:
        sides = set()

        for other in lines:
            if l == other:
                continue

            sides.update(l.pointsSides(other.verts))

            if SIDE_FRONT in sides and SIDE_BACK in sides:
                return False

    return True


ChoiseParams = collections.namedtuple("ChoiseParams", ["index", "axial", "front", "back", "cross", "imbalance"])

#TODO: Probably check against a few different cutoffs; the idea is that
#      a lower cutoff (gives a better balanced tree) might be worth a
#      few extra splits.
IMBALANCE_CUTOFF = 0.15


def _countSplits(lines, l):
    sides = []
    for ll in lines:
        if ll != l:
            sides.append(l.lineSide(ll))

    front = sides.count(SIDE_FRONT)
    back = sides.count(SIDE_BACK)
    cross = sides.count(SIDE_CROSS)

    return (front, back, cross)


def _chooseNodeLine(lines):
    len_ = float(len(lines))

    # sort lines by axial cases first
    axial = []
    nonaxial = []
    for l in lines:
        if l.isAxial():
            axial.append(l)
        else:
            nonaxial.append(l)
    lines = axial + nonaxial

    counts = []

    # find where each line lies with respect to each other
    for idx, l in enumerate(lines):
        front, back, cross = _countSplits(lines, l)
#FIXME: need to sub 1 from len_ because front & back don't include the line its self
# note div-by-zero; but shouldn't happen
        counts.append( ChoiseParams(idx, l.isAxial(), front, back, cross, abs(front - back) / len_) )

    # sort the candidates by how well they divide the space; ideally
    # we would get a line that divides the space exactly in half
    by_imbalance = sorted(counts, key=lambda x: x.imbalance)
    by_imbalance_axial = filter(lambda x: x.axial, by_imbalance)
    by_imbalance_nonaxial = filter(lambda x: not x.axial, by_imbalance)

    best_axial = None
    for cp in by_imbalance_axial:
        if cp.cross == 0 and 0 in [cp.front, cp.back]:
            # not a valid node if it doesn't divide the space
            continue
        if cp.imbalance > IMBALANCE_CUTOFF and best_axial is not None:
            break
        if best_axial is None:
            best_axial = cp
        elif cp.cross < best_axial.cross:
            best_axial = cp

    best_nonaxial = None
    for cp in by_imbalance_nonaxial:
        if cp.cross == 0 and 0 in [cp.front, cp.back]:
            # not a valid node if it doesn't divide the space
            continue
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

    if False:
        print best

    return lines[best.index]

#FIXME: Convexity test will probably have to change to properly handle
#       colinar lines creating a "non-convex" space
#       If this is done, we'll use _countSplits(). We should reuse the
#       results of this over to the node chooser so it's not done
#       twice.

def _recursiveBSP(lines):
    if _isConvex(lines):
        idx = len(b_leafs)
        b_leafs.append(lines)
        return idx | 0x80000000

#FIXME: *don't remove the line*; just use it as a splitter
#       it will always end up on its front side
#       maybe just save off the plane, or make a copy as it's used for
#       only geometry testing and nothing else
    node = _chooseNodeLine(lines)
    lines.remove(node)

    frontlines, backlines = node.splitLines(lines)

    if not frontlines:
        raise Exception("node chosen with no front space")
    if not backlines:
        raise Exception("node chosen with no back space")

    idx = len(b_nodes)
    b_nodes.append(None)

    n = {}
    n["node"] = node
    n["front"] = _recursiveBSP(frontlines)
    n["back"] = _recursiveBSP(backlines)

    b_nodes[idx] = n

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
    global o_verts

    vertexes = objs["VERTEXES"]
    linedefs = objs["LINEDEFS"]
    sidedefs = objs["SIDEDEFS"]
    sectors = objs["SECTORS"]

    b_nodes = []
    b_leafs = []

    o_verts = []

    _recursiveBSP(_createBLines())

    print "%d nodes" % len(b_nodes)
    print "%d leafs" % len(b_leafs)
