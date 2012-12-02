#ifndef __DMAP_H__
#define __DMAP_H__

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

#endif /* __DMAP_H__ */
