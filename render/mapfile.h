#ifndef __MAPFILE_H__
#define __MAPFILE_H__

/* on-disk map structures */

#define MAP_VERSION 2

struct dvertex_s
{
	float xyz[3];
};

struct dplane_s
{
	float normal[3];
	float dist;
};

/* Note 2 coplanar planes with opposing normals will be merged into just
 * one plane. One of the planes will have its normal and dist inverted,
 * and any object referencing the old plane will now be considered on
 * the reverse side. (eg: something on the front will now be on the back
 * side) */

struct dedge_s
{
	unsigned short verts[2];
};

struct dleaf_s
{
	short mins[3], maxs[3];
	unsigned short first_poly;
	unsigned short num_polys;
};

struct dnode_s
{
	short mins[3], maxs[3];
	unsigned short first_poly;
	unsigned short num_polys;

	unsigned short plane;
	unsigned short children[2]; /* back, front */
};

struct dpoly_s
{
	unsigned short plane;
	unsigned short side;

	unsigned short first_edge;
	unsigned short num_edges;

	unsigned short texinfo; /* -1 if a portal */
};

/* Polygon edges are just lists of ushorts, each representing an index
 * in the edge list. If the high bit is set, the edge runs backwards. */

struct dtexinfo_s
{
	char texname[16];
	short offs[2];
};

struct dmapheader_s
{
	char id[4];
	int version;
};

#endif /* __MAPFILE_H__ */

/* We can take a viewpoint/node side test and re-use it for the polys
 * that lie on the node for quicker backface culling. */
