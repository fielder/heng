#ifndef __R_DEFS_H__
#define __R_DEFS_H__

#include <stdint.h>

#include "map.h"


enum
{
	VPLANE_LEFT,
	VPLANE_RIGHT,
	VPLANE_TOP,
	VPLANE_BOTTOM,
};


struct viewplane_s
{
	float normal[3];
	float dist;

	int minmax_lookup[3];

	struct viewplane_s *next;
};


struct r_vars_s
{
	int debug;

	/* draw buffer */
	int w, h, pitch;
	uint8_t *screen;

	int framenum;

	/* camera defs */
	float center_x;
	float center_y;

	float fov_x; /* radians */
	float fov_y; /* radians */

	float dist;

	float pos[3];

	float angles[3]; /* radians */

	float xform[3][3]; /* world-to-camera */

	float left[3];
	float up[3];
	float forward[3];

	struct viewplane_s vplanes[4];
};


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
