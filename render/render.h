#ifndef __RENDER_H__
#define __RENDER_H__

#include <stdint.h>

struct r_vars_s
{
	/* draw buffer */
	int w, h, pitch;
	uint8_t *screen;

	/* camera defs */
	float center_x;
	float center_y;

	float fov_x; /* radians */
	float fov_y; /* radians */

	float near_dist;
	float far_dist;

	float pos[3];

	float angles[3]; /* radians */

	float xform[3][3]; /* world-to-camera */

	float left[3];
	float up[3];
	float forward[3];

	/* the corner-most rays terminating points */
	float far[4][3];

//	struct viewplane_s vplanes[4];
};

struct viewplane_s
{
	float normal[3];
	float dist;
	int type;
	int signbits;

	struct viewplane_s *next;
};

enum
{
	VPLANE_LEFT,
	VPLANE_TOP,
	VPLANE_RIGHT,
	VPLANE_BOTTOM
};

extern struct r_vars_s r_vars;

#endif /* __RENDER_H__ */
