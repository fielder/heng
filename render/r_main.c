#include <stdint.h>

#include "r_defs.h"

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
setupView (void)
{
	//...
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
