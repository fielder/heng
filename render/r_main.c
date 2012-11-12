#include <stdint.h>
#include <math.h>

#include "r_defs.h"
#include "vec.h"

struct r_buf_s r_buf;
struct r_view_s r_view;


void
setup (uint8_t *buf, int w, int h, int pitch)
{
	r_buf.screen = buf;
	r_buf.w = w;
	r_buf.h = h;
	r_buf.pitch = pitch;
}


void
setCamera (float fov_x, float pos[3], float angles[3])
{
	r_view.center_x = r_buf.w / 2.0 - 0.5;
	r_view.center_y = r_buf.h / 2.0 - 0.5;

	r_view.fov_x = fov_x;
	r_view.dist = (r_buf.w / 2.0) / tan(r_view.fov_x / 2.0);
	r_view.fov_y = 2.0 * atan((r_buf.h / 2.0) / r_view.dist);

	Vec_Copy (pos, r_view.pos);
	Vec_Copy (angles, r_view.angles);

	//TODO: view vecs
	//TODO: xform
	//TODO: view planes
}


void
drawPalette (void)
{
	int x, y;

	for (y = 0; y < 128 && y < r_buf.h; y++)
	{
		uint8_t *dest = r_buf.screen + y * r_buf.pitch;
		for (x = 0; x < 128 && x < r_buf.w; x++)
			*dest++ = ((y << 1) & 0xf0) + (x >> 3);
	}
}
