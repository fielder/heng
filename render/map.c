#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

#include "bswap.h"
#include "dmap.h"
#include "map.h"

struct map_s map;


void
LoadVertexes (const void *buf, int buflen)
{
	const struct dvertex_s *dv, *dend;
	int count = buflen / sizeof(*dv);
	struct vertex_s *v;

	v = map.verts = malloc (count * sizeof(*v));
	map.num_verts = count;

	dv = buf;
	dend = dv + count;
	while (dv != dend)
	{
		v->xyz[0] = dv->x;
		v->xyz[1] = dv->y;
		v->xyz[2] = dv->z;
		v++;

		dv++;
	}

	printf ("Loaded %d vertexes\n", map.num_verts);
}


void
LoadEdges (const void *buf, int buflen)
{
	const struct dedge_s *de, *dend;
	int count = buflen / sizeof(*de);
	struct edge_s *e;

	e = map.edges = malloc (count * sizeof(*e));
	map.num_edges = count;

	de = buf;
	dend = de + count;
	while (de != dend)
	{
		e->v[0] = de->v1;
		e->v[1] = de->v2;
		e++;

		de++;
	}

	printf ("Loaded %d edges\n", map.num_edges);
}


void
LoadVertexes_2D (const void *buf, int buflen)
{
	const struct dvertex2d_s *dv, *dend;
	int count = buflen / sizeof(*dv);
	struct vertex2d_s *v;

	v = map.verts_2d = malloc (count * sizeof(*v));
	map.num_verts_2d = count;

	dv = buf;
	dend = dv + count;
	while (dv != dend)
	{
		v->xy[0] = dv->x;
		v->xy[1] = dv->y;
		v++;

		dv++;
	}

	printf ("Loaded %d 2d vertexes\n", map.num_verts_2d);
}


void
LoadLines_2D (const void *buf, int buflen)
{
	const struct dline2d_s *dl, *dend;
	int count = buflen / sizeof(*dl);
	struct line2d_s *l;

	l = map.lines_2d = malloc (count * sizeof(*l));
	map.num_lines_2d = count;

	dl = buf;
	dend = dl + count;
	while (dl != dend)
	{
		l->v[0] = &map.verts_2d[dl->v1];
		l->v[1] = &map.verts_2d[dl->v2];
		l++;

		dl++;
	}

	printf ("Loaded %d 2d lines\n", map.num_lines_2d);
}


void
LoadLeafs_2D (const void *buf, int buflen)
{
}


//TODO: free stuff
