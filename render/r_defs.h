#ifndef __R_DEFS_H__
#define __R_DEFS_H__

#include "map.h"


/* clipped and projected edge */
struct drawedge_s
{
	struct drawedge_s *next; /* in v-sorted list of edges for the poly */

	int top, bottom;
	int u, du; /* 12.20 fixed-point format */
	/* no need for a dv as it's always 1 pixel */
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
	struct drawedge_s *edges;

	struct drawspan_s *spans;
	int num_spans;

	struct mpoly_s *mpoly;

	//TODO: texture mapping stuff
};

#endif /* __R_DEFS_H__ */
