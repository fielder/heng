#ifndef __R_DEFS_H__
#define __R_DEFS_H__

#include "map.h"

#define BACKFACE_DIST 0.01

/* clipped and projected edge */
struct drawedge_s
{
	struct medge_s *owner;
	struct drawedge_s *next; /* in v-sorted list of edges for the poly */

	int top, bottom;
	int u, du; /* 12.20 fixed-point format */

	int is_right;
};


/* emitted polygon span */
struct drawspan_s
{
	short u, v;
	short len;
};


/* draw polys */
struct drawpoly_s
{
	struct drawedge_s *edges[2]; /* left/right on the screen */

	struct drawspan_s *spans;
	int num_spans;

	struct mpoly_s *mpoly;

	//TODO: texture mapping stuff
};

#endif /* __R_DEFS_H__ */
