#include <stdint.h>
#include <stdlib.h>

#include "dmap.h"
#include "map.h"
#include "bswap.h"

struct map_s map;


void
loadVertexes_2D (const uint8_t *buf, int buflen)
{
	const uint8_t *end = buf + buflen;
	int count = buflen / 8;
	struct vertex2d_s *v;

	v = map.verts_2d = malloc (count * sizeof(*v));
	map.num_verts_2d = count;

	while (buf != end)
	{
		float x, y;
		//FIXME: swap
		x = ((float *)buf)[0];
		y = ((float *)buf)[1];
		buf += 8;

		v->xy[0] = x;
		v->xy[1] = y;
		v++;
	}
}

//TODO: free stuff
