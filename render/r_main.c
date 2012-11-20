#include <stdio.h>
#include <stdint.h>
#include <math.h>
#include <string.h>

#include "r_defs.h"
#include "vec.h"

static void
initCamera (float);

static void
cameraChanged (void);

static void
transformVec (float xform[3][3], const float v[3], float out[3]);

struct r_defs_s r_defs;


void
setup (uint8_t *buf, int w, int h, int pitch, float fov_x)
{
	r_defs.screen = buf;
	r_defs.w = w;
	r_defs.h = h;
	r_defs.pitch = pitch;

	initCamera (fov_x);
}


static void
initCamera (float fov_x)
{
	r_defs.center_x = r_defs.w / 2.0 - 0.5;
	r_defs.center_y = r_defs.h / 2.0 - 0.5;

	r_defs.fov_x = fov_x;
	r_defs.near_dist = (r_defs.w / 2.0) / tan(r_defs.fov_x / 2.0);
	printf ("%g\n",r_defs.near_dist );
	r_defs.far_dist = 64 * 48;
	r_defs.fov_y = 2.0 * atan((r_defs.h / 2.0) / r_defs.near_dist);

	Vec_Clear (r_defs.pos);
	Vec_Clear (r_defs.angles);

//	r_defs.angles[1] = M_PI; /* start off looking to +z axis */

	cameraChanged ();
}


static void
cameraChanged (void)
{
	float cam2world[3][3];
	float v[3];
	float x, y, z, xadj, yadj;
	int i;

	/* make transformation matrix */
	Vec_Copy (r_defs.angles, v);
	Vec_Scale (v, -1.0);
	Vec_AnglesMatrix (v, r_defs.xform, ROT_MATRIX_ORDER_XYZ);

	/* We're looking down the -z axis, and our projection calculation
	 * assumes greater z is further away. So negate z values so
	 * positive z objects are behind the camera. */
	Vec_Scale (r_defs.xform[2], -1.0);

	/* get view vectors */
	Vec_Copy (r_defs.xform[0], r_defs.right);
	Vec_Copy (r_defs.xform[1], r_defs.up);
	Vec_Copy (r_defs.xform[2], r_defs.forward);

	//TODO: setup view planes

	x = r_defs.far_dist * tan(r_defs.fov_x / 2.0);
	y = r_defs.far_dist * tan(r_defs.fov_y / 2.0);
	z = -r_defs.far_dist; /* default view looks down the -z axis */

	/* The adjustment to get to the center of a pixel on the far plane
	 * should be larger, as the screen pixels projected onto the back
	 * plane are much larger. */
	xadj = 0.5 * (x / (r_defs.w / 2.0));
	yadj = 0.5 * (y / (r_defs.h / 2.0));
	// top-left
	r_defs.far[0][0] = -x + xadj;
	r_defs.far[0][1] = y - yadj;
	r_defs.far[0][2] = z;
	// top-right
	r_defs.far[1][0] = x - xadj;
	r_defs.far[1][1] = y - yadj;
	r_defs.far[1][2] = z;
	// bottom-left
	r_defs.far[2][0] = -x + xadj;
	r_defs.far[2][1] = -y + yadj;
	r_defs.far[2][2] = z;
	// bottom-right
	r_defs.far[3][0] = x - xadj;
	r_defs.far[3][1] = -y + yadj;
	r_defs.far[3][2] = z;

	/* move corner rays to world space */
	Vec_AnglesMatrix (r_defs.angles, cam2world, ROT_MATRIX_ORDER_ZYX);
	for (i = 0; i < 4; i++)
	{
		transformVec (cam2world, r_defs.far[i], v);
		Vec_Add (r_defs.pos, v, r_defs.far[i]);
	}
}


void
cameraRotatePixels (float dx, float dy)
{
	/* using right-handed coordinate system, so positive yaw goes
	 * left across the screen and positive roll goes up */
	r_defs.angles[YAW] += r_defs.fov_x * (-dx / r_defs.w);
	r_defs.angles[PITCH] += r_defs.fov_y * (-dy / r_defs.h);

	/* restrict camera angles */
	if (r_defs.angles[PITCH] > M_PI / 2.0)
		r_defs.angles[PITCH] = M_PI / 2.0;
	if (r_defs.angles[PITCH] < -M_PI / 2.0)
		r_defs.angles[PITCH] = -M_PI / 2.0;

	while (r_defs.angles[YAW] >= M_PI * 2.0)
		r_defs.angles[YAW] -= M_PI * 2.0;
	while (r_defs.angles[YAW] < 0.0)
		r_defs.angles[YAW] += M_PI * 2.0;

	cameraChanged ();
}


void
cameraThrust (float right, float up, float forward)
{
	float v[3];

	Vec_Copy (r_defs.right, v);
	Vec_Scale (v, right);
	Vec_Add (r_defs.pos, v, r_defs.pos);

	Vec_Copy (r_defs.up, v);
	Vec_Scale (v, up);
	Vec_Add (r_defs.pos, v, r_defs.pos);

	Vec_Copy (r_defs.forward, v);
	Vec_Scale (v, forward);
	Vec_Add (r_defs.pos, v, r_defs.pos);

	cameraChanged ();
}


static void
transformVec (float xform[3][3], const float v[3], float out[3])
{
	int i;

	for (i = 0; i < 3; i++)
		out[i] = Vec_Dot (xform[i], v);
}


void
clearScreen (void)
{
	int y;

	if (((uintptr_t)r_defs.screen & 0x3) == 0 && (r_defs.w % 4) == 0)
	{
		for (y = 0; y < r_defs.h; y++)
		{
			int w2 = r_defs.w >> 2;
			uint32_t *dest = (uint32_t *)(r_defs.screen + y * r_defs.pitch);
			while (w2--)
				*dest++ = 0;
		}
	}
	else
	{
		for (y = 0; y < r_defs.h; y++)
			memset (r_defs.screen + y * r_defs.pitch, 0, r_defs.w);
	}
}


static void
drawPoint3D (float p[3])
{
	float local[3], v[3];
	float zi;
	int uu, vv;

	Vec_Subtract (p, r_defs.pos, local);
	transformVec (r_defs.xform, local, v);
	if (v[2] > 0.0)
	{
		zi = 1.0 / v[2];
		uu = (int)(r_defs.center_x + r_defs.near_dist * zi * v[0]);
		vv = (int)(r_defs.center_y - r_defs.near_dist * zi * v[1]);
		if (uu >= 0 && uu < r_defs.w && vv >= 0 && vv < r_defs.h)
			r_defs.screen[vv * r_defs.pitch + uu] = 4;
	}
}


static void
drawFrustum (void)
{
	int i;
	for (i = 0; i < 4; i++)
		drawPoint3D (r_defs.far[i]);
}


static int
testHit (const float normal[3], float dist, const float s[3], const float e[3])
{
	float ds, de, frac;
	float p[3];

	ds = (s[0] * normal[0] + s[1] * normal[1] + s[2] * normal[2]) - dist;
	de = (e[0] * normal[0] + e[1] * normal[1] + e[2] * normal[2]) - dist;

	if ((ds <= 0 && de <= 0) || (ds >= 0 && de >= 0))
		return 0;

	frac = ds / (ds - de);
	p[0] = s[0] + frac * (e[0] - s[0]);
	p[1] = s[1] + frac * (e[1] - s[1]);
	p[2] = s[2] + frac * (e[2] - s[2]);

	return p[0] >= 0 && p[0] <= 32 && p[2] >= -128 && p[2] <= -32;
}


static void
drawPoly (void)
{
	float far_dx[3], far_dy[3];
	float end[3], e[3];
	int x, y;
	uint8_t *dest;

	float normal[3], dist;

	normal[0] = 0.0;
	normal[1] = 1.0;
	normal[2] = 0.0;
	dist = -128.0;

	if (Vec_Dot(normal, r_defs.pos) - dist < 0)
		return;

	far_dx[0] = (r_defs.far[1][0] - r_defs.far[0][0]) / (r_defs.w - 1);
	far_dx[1] = (r_defs.far[1][1] - r_defs.far[0][1]) / (r_defs.w - 1);
	far_dx[2] = (r_defs.far[1][2] - r_defs.far[0][2]) / (r_defs.w - 1);
	far_dy[0] = (r_defs.far[2][0] - r_defs.far[0][0]) / (r_defs.h - 1);
	far_dy[1] = (r_defs.far[2][1] - r_defs.far[0][1]) / (r_defs.h - 1);
	far_dy[2] = (r_defs.far[2][2] - r_defs.far[0][2]) / (r_defs.h - 1);

	dest = r_defs.screen;

	Vec_Copy (r_defs.far[0], end);
	for (y = 0; y < r_defs.h; y++)
	{
		e[0] = end[0];
		e[1] = end[1];
		e[2] = end[2];
		for (x = 0; x < r_defs.w; x++)
		{
			if (testHit(normal, dist, r_defs.pos, e))
				dest[x] = 4;

			e[0] += far_dx[0];
			e[1] += far_dx[1];
			e[2] += far_dx[2];
		}	
		end[0] += far_dy[0];
		end[1] += far_dy[1];
		end[2] += far_dy[2];

		dest += r_defs.pitch;
	}	
}


void
drawWorld (void)
{
	float v[3];
	int x, z;
	for (z = 0; z < 16; z++)
	{
		for (x = 0; x < 16; x++)
		{
			v[0] = x;
			v[1] = 0.0;
			v[2] = z;
			drawPoint3D(v);
		}
	}
	for (x = 0; x < 128; x++)
	{
		v[0] = x; v[1] = 0.0; v[2] = 0.0; drawPoint3D(v);
		v[0] = 0.0; v[1] = x; v[2] = 0.0; drawPoint3D(v);
		v[0] = 0.0; v[1] = 0.0; v[2] = x; drawPoint3D(v);
	}

	drawFrustum ();

	drawPoly ();
}


void
drawPalette (void)
{
	int x, y;

	for (y = 0; y < 128 && y < r_defs.h; y++)
	{
		uint8_t *dest = r_defs.screen + y * r_defs.pitch;
		for (x = 0; x < 128 && x < r_defs.w; x++)
			*dest++ = ((y << 1) & 0xf0) + (x >> 3);
	}
}


void
drawLine (int x1, int y1, int x2, int y2, int c)
{
	int x, y;
	int dx, dy;
	int sx, sy;
	int ax, ay;
	int d;

	if (0)
	{
		if (	x1 < 0 || x1 >= r_defs.w ||
			x2 < 0 || x2 >= r_defs.w ||
			y1 < 0 || y1 >= r_defs.h ||
			y2 < 0 || y2 >= r_defs.h )
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
			r_defs.screen[y * r_defs.pitch + x] = c;
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
			r_defs.screen[y * r_defs.pitch + x] = c;
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
