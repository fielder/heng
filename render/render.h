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
	VPLANE_TOP,
	VPLANE_BOTTOM,
	VPLANE_LEFT,
	VPLANE_RIGHT,
};

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

	float dist;

	float pos[3];

	float angles[3]; /* radians */

	float xform[3][3]; /* world-to-camera */

	float left[3];
	float up[3];
	float forward[3];

	struct viewplane_s vplanes[4];

	int framenum;
};

extern struct r_vars_s r_vars;


extern void
Setup (uint8_t *buf, int w, int h, int pitch, float fov_x);

extern void
CameraRotatePixels (float screen_dx, float screen_dy);

extern void
CameraThrust (float left, float up, float forward);

extern void
DrawWorld (void);

extern void
DrawSprite (const void *lump, int x, int y);

extern void
DrawPixmap(const void *pixels, int w, int h, int x, int y);

extern void
DrawSpriteToPixmap (const void *lump, void *out);

#endif /* __RENDER_H__ */
