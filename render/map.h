#ifndef __MAP_H__
#define __MAP_H__

/* in-memory map structures */

struct mvertex_s
{
	float xyz[3];
};

enum
{
	PLANE_X, /* normal (1, 0, 0) */
	PLANE_Y, /* normal (0, 1, 0) */
	PLANE_Z, /* normal (0, 0, 1) */
	PLANE_XY, /* normal (x, y, 0) */
	PLANE_XZ, /* normal (x, 0, z) */
	PLANE_YZ, /* normal (0, y, z) */
	PLANE_OTHER
};

struct mplane_s
{
	float normal[3];
	float dist;
	short type;
	short signbits;
};

struct medge_s
{
	unsigned short v[2];
	unsigned int cache_offset;
};

struct msector_s
{
	int lightlevel;
	int lightstyle;
	int contents;
};

struct mface_s
{
	struct msector_s *sector;
	//TODO: texture, has transparent pixels
	//TODO: vecs
};

struct msurface_s
{
	struct mplane_s *plane;
	int side;

	unsigned int *edges; /* in surface edge list */
	int num_edges;

	struct mface_s *face; /* unused for portal surfaces */
};

#define NODEFLAG_LEAF 0x80000000

struct mleaf_s
{
	int flags;
	short mins[3], maxs[3];

	struct msurface_s *surfaces;
	int num_surfaces;
};

struct mnode_s
{
	int flags;
	short mins[3], maxs[3];

	struct mplane_s *plane;

	struct msurface_s *surfaces;
	int num_surfaces;
	int num_portals;

	void *children[2]; /* front, back */
};

#if 0
struct vertex2d_s
{
	float xy[2];
};

struct line2d_s
{
	struct vertex2d_s *v[2];
};

struct leaf2d_s
{
	struct line2d_s *lines;
	int numlines;
};
#endif

struct map_s
{
	struct mvertex_s *verts
	int num_verts;

	struct mplane_s *planes
	int num_planes;

	struct medge_s *edges
	int num_edges;

	struct msector_s *sectors
	int num_sectors;

	struct mface_s *faces
	int num_faces;

	struct msurface_s *surfaces
	int num_surfaces;

	struct mleaf_s *leafs
	int num_leafs;

	struct mnode_s *nodes
	int num_nodes;

	unsigned int *surfedges;
	int num_surfedges;

#if 0
	struct vertex2d_s *verts_2d;
	int num_verts_2d;

	struct line2d_s *lines_2d;
	int num_lines_2d;

	struct leaf2d_s *leafs_2d;
	int num_leafs_2d;
#endif
};

extern struct map_s map;

#endif /* __MAP_H__ */
