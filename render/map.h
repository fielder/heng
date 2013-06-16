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
	unsigned int cache_offset;
};

struct mplane_s
{
	float normal[3];
	float dist;
	int signbits;
	int type;
};

struct mpoly_s
{
	struct mplane_s *plane;
	int side;

	unsigned short *edges;
	int num_edges;
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

#endif /* __MAP_H__ */
