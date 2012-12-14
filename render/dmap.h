#ifndef __DMAP_H__
#define __DMAP_H__

/* map structures as formatted on disk */

struct dplane_s
{
	float normal[3];
	float dist;
};

struct dvertex_s
{
	float x, y, z;
};

struct dedge_s
{
	unsigned short v1, v2;
};

struct dsector_s
{
	unsigned short lightlevel;
	unsigned short lightstyle;
	unsigned short contents;
};

struct dface_s
{
	unsigned short sector;
	//TODO: texture, has transparent pixels
	//TODO: vecs
};

struct dsurface_s
{
	unsigned int first_surfedge;
	short num_surfedges;

	unsigned short plane;
	short side;

	unsigned short face; /* -1 for portals */
};

struct dleaf_s
{
	short mins[3];
	short maxs[3];

	unsigned short first_surface;
	short num_surface;
};

struct dnode_s
{
	short mins[3];
	short maxs[3];

	/* all on-node surfaces must reference the node's plane */
	unsigned short first_surface;
	short num_surface;

	unsigned short plane;

	unsigned short front, back; /* high  bit if a leaf */
};

//...
//...

struct dvertex2d_s
{
	float x, y;
};

struct dline2d_s
{
	int v1, v2;
};

struct dleaf2d_s
{
	int firstline;
	int numlines;
};

#endif /* __DMAP_H__ */
