#ifndef __MAP_H__
#define __MAP_H__

/* in-memory structures */

#if 0
enum
{
	PLANE_X, /* normal (1, 0, 0) */
	PLANE_Y, /* normal (0, 1, 0) */
	PLANE_Z, /* normal (0, 0, 1) */
	PLANE_XY, /* normal (x, y, 0) */
	PLANE_YZ, /* normal (0, y, z) */
	PLANE_XZ, /* normal (x, 0, z) */
	PLANE_OTHER
};

struct mplane_s
{
	float normal[3];
	float dist;
	unsigned char type;
	unsigned char signbits;
	unsigned char pad[2];
};

#define NODEFLAGS_LEAF 0x80000000

struct mnode_s
{
	/* shared with leaf structure */
	unsigned int flags;
	short mins[3];
	short maxs[3];

	/* specific to node */
	void *children[2]; /* could be node or leaf */
	struct mplane_s *plane;
};

struct mleaf_s
{
	/* shared with node structure */
	unsigned int flags;
	short mins[3];
	short maxs[3];

	/* specific to leaf */
	unsigned int *planes;
	//TODO: light value, light style
};

struct msurface_s
{
	unsigned int *eplanes;
	int num_eplanes;
	struct mtexinfo_s *texinfo;
};

struct mtexinfo_s
{
	int xoff, yoff;
	struct mtex_s *tex;
};

struct mtex_s
{
	int w, h;
	int has_transparent;
	unsigned char *pixels;
};

struct mthing_s
{
	float pos[3];
	float angle;
	int type;
	int flags;
};

struct map_s
{
	struct mplane_s *planes;
	int num_planes;

	struct mnode_s *nodes;
	int num_nodes;

	struct msurface_s *surfs;
	int num_surfs;

	struct mtexinfo_s *texinfos;
	int num_texinfos;

	struct mtex_s *textures;
	int num_textures;

	struct mthing_s *things;
	int num_things;
};
#endif

struct vertex_s
{
	float xyz[3];
};

struct edge_s
{
	unsigned int v[2];
	//TODO: cache
};

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

struct map_s
{
	struct vertex_s *verts;
	int num_verts;

	struct edge_s *edges;
	int num_edges;

	struct vertex2d_s *verts_2d;
	int num_verts_2d;

	struct line2d_s *lines_2d;
	int num_lines_2d;

	struct leaf2d_s *leafs_2d;
	int num_leafs_2d;
};

extern struct map_s map;

#endif /* __MAP_H__ */
