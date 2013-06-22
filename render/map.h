#ifndef __MAP_H__
#define __MAP_H__

/* in-memory map structures */

struct mvertex_s
{
	float xyz[3];
};

struct medge_s
{
	unsigned short v[2];
	unsigned int cache_index;
};

struct mplane_s
{
	float normal[3];
	float dist;
	int signbits;
	int type;
};

enum
{
	PLANE_X, /* (1, 0, 0) */
	PLANE_Y, /* (0, 1, 0) */
	PLANE_Z, /* (0, 0, 1) */
	PLANE_OTHER, /* non-axial planes */
};

enum
{
	POLY_SIDE_FRONT,
	POLY_SIDE_BACK,
};

struct mpoly_s
{
	struct mplane_s *plane;
	int side;

	unsigned short *edges;
	int num_edges;
};

struct mleaf_s
{
	int is_leaf;
	short mins[3], maxs[3];
	struct mpoly_s *polys;
	int num_polys;
};

struct mnode_s
{
	int is_leaf;
	short mins[3], maxs[3];
	struct mpoly_s *polys;
	int num_polys;

	struct mplane_s *plane;
	void *children[2]; /* back, front */
};

struct map_s
{
	struct mvertex_s *verts;
	int num_verts;

	struct medge_s *edges;
	int num_edges;

	struct mplane_s *planes;
	int num_planes;

	unsigned short *polyedges;
	int num_polyedges;

	struct mpoly_s *polys;
	int num_polys;

	struct mleaf_s *leafs;
	int num_leafs;

	struct mnode_s *nodes;
	int num_nodes;
};

extern struct map_s map;


extern void
Map_LoadVertices (const void *buf, int bufsize);

extern void
Map_LoadEdges (const void *buf, int bufsize);

extern void
Map_LoadPlanes (const void *buf, int bufsize);

extern void
Map_LoadPolyEdges (const void *buf, int bufsize);

extern void
Map_LoadPolys (const void *buf, int bufsize);

extern void
Map_LoadLeafs (const void *buf, int bufsize);

extern void
Map_LoadNodes (const void *buf, int bufsize);

#endif /* __MAP_H__ */
