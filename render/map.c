#include <stdint.h>
#include <stdlib.h>

#include "bswap.h"
#include "dmap.h"
#include "map.h"

struct map_s map;


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
}


void
LoadLeafs_2D (const void *buf, int buflen)
{
}


//TODO: free stuff
