#include <stdint.h>
#include <string.h>

#include "cdefs.h"
#include "vec.h"

#include "render.h"


void
PutPixel (int x, int y, int c)
{
	if (x >= 0 && x < r_vars.w && y >= 0 && y < r_vars.h)
		r_vars.screen[y * r_vars.pitch + x] = c;
}


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


static int
ProjectPoint (const float p[3], int *u, int *v)
{
	float local[3], out[3], zi;

	Vec_Subtract (p, r_vars.pos, local);
	Vec_Transform (r_vars.xform, local, out);
	if (out[2] <= 0.0)
	{
		/*
		printf("(%g %g %g) -> (%g %g %g)\n",p[0],p[1],p[2],out[0],out[1],out[2]);
		fflush(stdout);
		*/
		return 0;
	}

	zi = 1.0 / out[2];
	*u = (r_vars.w / 2.0) - r_vars.dist * zi * out[0];
	*v = (r_vars.h / 2.0) - r_vars.dist * zi * out[1];
	//FIXME: Sometimes we'll get a point nearly right on the eye,
	//	allowing the zi to become fairly large (1.5 to 30 range)
	//	and projecting off the screen.
	//	This should never happen when drawing polys, as the
	//	backface culling should do so on an epsilon, so an edge
	//	will never run almost straight through the eye.
	if (*u < 0) *u = 0;
	if (*u >= r_vars.w) *u = r_vars.w - 1;
	if (*v < 0) *v = 0;
	if (*v >= r_vars.h) *v = r_vars.h - 1;

	return 1;
}


static int
ClipLine3D (const float normal[3], float dist, float verts[2][3], float out[2][3])
{
	float d1, d2, frac;

	d1 = Vec_Dot(verts[0], normal) - dist;
	d2 = Vec_Dot(verts[1], normal) - dist;

	if (d1 < PLANE_DIST_EPSILON && d2 < PLANE_DIST_EPSILON)
	{
		return 0;
	}
	else if (d1 >= PLANE_DIST_EPSILON && d2 >= PLANE_DIST_EPSILON)
	{
		Vec_Copy (verts[0], out[0]);
		Vec_Copy (verts[1], out[1]);
	}
	else if (d1 < 0.0)
	{
		frac = d1 / (d1 - d2);
		out[0][0] = verts[0][0] + frac * (verts[1][0] - verts[0][0]);
		out[0][1] = verts[0][1] + frac * (verts[1][1] - verts[0][1]);
		out[0][2] = verts[0][2] + frac * (verts[1][2] - verts[0][2]);
		out[1][0] = verts[1][0];
		out[1][1] = verts[1][1];
		out[1][2] = verts[1][2];
	}
	else
	{
		frac = d2 / (d2 - d1);
		out[0][0] = verts[1][0] + frac * (verts[0][0] - verts[1][0]);
		out[0][1] = verts[1][1] + frac * (verts[0][1] - verts[1][1]);
		out[0][2] = verts[1][2] + frac * (verts[0][2] - verts[1][2]);
		out[1][0] = verts[0][0];
		out[1][1] = verts[0][1];
		out[1][2] = verts[0][2];
	}

	return 1;
}


void
DrawLine3D (const float p1[3], const float p2[3], int c)
{
	float verts[2][2][3];
	int clipidx = 0;
	int i;
	struct viewplane_s *vp;

	Vec_Copy (p1, verts[clipidx][0]);
	Vec_Copy (p2, verts[clipidx][1]);

	for (i = 0, vp = &r_vars.vplanes[0]; i < 4; i++, vp++)
	{
		if (!ClipLine3D(vp->normal, vp->dist, verts[clipidx], verts[!clipidx]))
			return;
		clipidx ^= 1;
	}

	{
		int u1=0, v1=0, u2=0, v2=0;
		if (!ProjectPoint(verts[clipidx][0], &u1, &v1))
			return;
		if (!ProjectPoint(verts[clipidx][1], &u2, &v2))
			return;
		DrawLine (u1, v1, u2, v2, c);
	}
}


void
DrawGrid (int size, int color)
{
	int i;
	float a[3], b[3];

	for (i = 0; i <= size; i += 64)
	{
		/* X-Z plane */
		a[0] = i; a[1] = 0; a[2] = 0;
		b[0] = i; b[1] = 0; b[2] = size;
		DrawLine3D (a, b, color);
		a[0] = 0; a[1] = 0; a[2] = i;
		b[0] = size; b[1] = 0; b[2] = i;
		DrawLine3D (a, b, color);

		/* X-Y plane */
		a[0] = i; a[1] = 0; a[2] = 0;
		b[0] = i; b[1] = size; b[2] = 0;
		DrawLine3D (a, b, color - 4);
		a[0] = 0; a[1] = i; a[2] = 0;
		b[0] = size; b[1] = i; b[2] = 0;
		DrawLine3D (a, b, color - 4);

		/* Z-Y plane */
		a[0] = 0; a[1] = 0; a[2] = i;
		b[0] = 0; b[1] = size; b[2] = i;
		DrawLine3D (a, b, color - 8);
		a[0] = 0; a[1] = i; a[2] = 0;
		b[0] = 0; b[1] = i; b[2] = size;
		DrawLine3D (a, b, color - 4);
	}
}
