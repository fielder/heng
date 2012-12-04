#ifndef __DMAP_H__
#define __DMAP_H__

/* map structures as formatted on disk */

struct dvertex_s
{
	float x, y, z;
};

struct dedge_s
{
	unsigned int v1, v2;
};

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
