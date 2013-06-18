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

#define POLY_SIDE_FRONT 0
#define POLY_SIDE_BACK 1

struct mpoly_s
{
	struct mplane_s *plane;
	int side;

	unsigned short *edges;
	int num_edges;
};

struct mleaf_s
{
	int xxx;
	//TODO: ...
};

struct mnode_s
{
	int xxx;
	//TODO: ...
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
