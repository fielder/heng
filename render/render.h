#ifndef __RENDER_H__
#define __RENDER_H__

#include <stdint.h>

struct viewplane_s
{
	float normal[3];
	float dist;

	struct viewplane_s *next;
};

enum
{
	VPLANE_LEFT,
	VPLANE_RIGHT,
	VPLANE_TOP,
	VPLANE_BOTTOM,
};

struct r_vars_s
{
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

extern struct r_vars_s r_vars;


extern void
SetupBuffer (uint8_t *buf, int w, int h, int pitch);

extern void
SetupProjection (float fov_x);

extern void
SetCamera (float pos[3], float angles[3]);

extern void
DrawWorld (void);

#endif /* __RENDER_H__ */
