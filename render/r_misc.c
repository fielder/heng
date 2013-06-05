#include <stdint.h>
#include <string.h>

#include "render.h"
#include "r_misc.h"


void
ClearScreen (void)
{
	int y;

	if (((uintptr_t)r_vars.screen & 0x3) == 0 && (r_vars.w & 0x3) == 0)
	{
		for (y = 0; y < r_vars.h; y++)
		{
			int w2 = r_vars.w >> 2;
			uint32_t *dest = (uint32_t *)(r_vars.screen + y * r_vars.pitch);
			while (w2--)
				*dest++ = 0;
		}
	}
	else
	{
		for (y = 0; y < r_vars.h; y++)
			memset (r_vars.screen + y * r_vars.pitch, 0, r_vars.w);
	}
}


void
DrawPalette (void)
{
	int x, y;

	for (y = 0; y < 128 && y < r_vars.h; y++)
	{
		uint8_t *dest = r_vars.screen + y * r_vars.pitch;
		for (x = 0; x < 128 && x < r_vars.w; x++)
			*dest++ = ((y << 1) & 0xf0) + (x >> 3);
	}
}


void
DrawLine (int x1, int y1, int x2, int y2, int c)
{
	int x, y;
	int dx, dy;
	int sx, sy;
	int ax, ay;
	int d;

	if (0)
	{
		if (	x1 < 0 || x1 >= r_vars.w ||
			x2 < 0 || x2 >= r_vars.w ||
			y1 < 0 || y1 >= r_vars.h ||
			y2 < 0 || y2 >= r_vars.h )
		{
			return;
		}
	}

	dx = x2 - x1;
	ax = 2 * (dx < 0 ? -dx : dx);
	sx = dx < 0 ? -1 : 1;

	dy = y2 - y1;
	ay = 2 * (dy < 0 ? -dy : dy);
	sy = dy < 0 ? -1 : 1;

	x = x1;
	y = y1;

	if (ax > ay)
	{
		d = ay - ax / 2;
		while (1)
		{
			r_vars.screen[y * r_vars.pitch + x] = c;
			if (x == x2)
				break;
			if (d >= 0)
			{
				y += sy;
				d -= ax;
			}
			x += sx;
			d += ay;
		}
	}
	else
	{
		d = ax - ay / 2;
		while (1)
		{
			r_vars.screen[y * r_vars.pitch + x] = c;
			if (y == y2)
				break;
			if (d >= 0)
			{
				x += sx;
				d -= ay;
			}
			y += sy;
			d += ax;
		}
	}
}
