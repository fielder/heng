#ifndef __R_DEFS_H__
#define __R_DEFS_H__

#include "map.h"

#define BACKFACE_DIST 0.01

enum
{
	CPLANES_TOP_BOTTOM,
	CPLANES_LEFT_RIGHT,
};

enum
{
	EDGE_LR_LEFT = 0x1,
	EDGE_LR_RIGHT = 0x2,
	EDGE_LR_VISIBLE = 0x4,
};

/* clipped and projected edge */
struct drawedge_s
{
	struct medge_s *owner;
	struct drawedge_s *next; /* in v-sorted list of edges for the poly */

	int top, bottom;
	int u, du; /* 12.20 fixed-point format */

	int lr_flags;
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
