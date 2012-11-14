#ifndef __R_DEFS_H__
#define __R_DEFS_H__

#include <stdint.h>

struct r_defs_s
{
	/* draw buffer */
	int w, h, pitch;
	uint8_t *screen;

	/* camera defs */
	float center_x;
	float center_y;

	float fov_x; /* radians */
	float fov_y; /* radians */

	float dist;

	float pos[3];

	float angles[3]; /* radians */

	float xform[3][3]; /* world-to-camera */

	float right[3];
	float up[3];
	float forward[3];

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

extern struct r_defs_s r_defs;

/* ================================================================== */

struct r_patch_s
{
	short width;
	short height;
	short leftoffset; /* pixels to the left of origin */
	short topoffset; /* pixels below the origin */
	int columnofs[0]; /* variable sized */
};

struct r_post_s
{
	uint8_t topdelta; /* 0xff is last post in a column */
	uint8_t length; /* <length> data bytes follow */
};

#endif /* __R_DEFS_H__ */
