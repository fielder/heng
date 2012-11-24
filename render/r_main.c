#include <stdint.h>
#include <math.h>
#include <string.h>

#include "render.h"
#include "vec.h"

struct r_vars_s r_vars;


static void
CameraChanged (void)
{
	float cam2world[3][3];
	float v[3];
	float x, y, z, xadj, yadj;
	int i;

	/* make transformation matrix */
	Vec_Copy (r_vars.angles, v);
	Vec_Scale (v, -1.0);
	Vec_AnglesMatrix (v, r_vars.xform, ROT_MATRIX_ORDER_XYZ);

	/* get view vectors */
	Vec_Copy (r_vars.xform[0], r_vars.left);
	Vec_Copy (r_vars.xform[1], r_vars.up);
	Vec_Copy (r_vars.xform[2], r_vars.forward);

	/* Find the screen's corner-most pixel rays in world space.
	 * Note that screen pixels projected to the back of the view
	 * frustum are large. So, the center of the pixel will be
	 * adjusted inward from the frustum edge accordingly.
	 */
	x = r_vars.far_dist * tan(r_vars.fov_x / 2.0);
	y = r_vars.far_dist * tan(r_vars.fov_y / 2.0);
	z = r_vars.far_dist;

	xadj = 0.5 * (x / (r_vars.w / 2.0));
	yadj = 0.5 * (y / (r_vars.h / 2.0));
	// top-left
	r_vars.far[0][0] = x - xadj;
	r_vars.far[0][1] = y - yadj;
	r_vars.far[0][2] = z;
	// top-right
	r_vars.far[1][0] = -x + xadj;
	r_vars.far[1][1] = y - yadj;
	r_vars.far[1][2] = z;
	// bottom-left
	r_vars.far[2][0] = x - xadj;
	r_vars.far[2][1] = -y + yadj;
	r_vars.far[2][2] = z;
	// bottom-right
	r_vars.far[3][0] = -x + xadj;
	r_vars.far[3][1] = -y + yadj;
	r_vars.far[3][2] = z;

	/* move corner rays to world space */
	Vec_AnglesMatrix (r_vars.angles, cam2world, ROT_MATRIX_ORDER_ZYX);
	for (i = 0; i < 4; i++)
	{
		Vec_Transform (cam2world, r_vars.far[i], v);
		Vec_Add (r_vars.pos, v, r_vars.far[i]);
	}

	//TODO: setup view planes
}


static void
InitCamera (float fov_x)
{
	r_vars.center_x = r_vars.w / 2.0 - 0.5;
	r_vars.center_y = r_vars.h / 2.0 - 0.5;

	r_vars.fov_x = fov_x;
	r_vars.near_dist = (r_vars.w / 2.0) / tan(r_vars.fov_x / 2.0);
	r_vars.far_dist = 64 * 48;
	r_vars.fov_y = 2.0 * atan((r_vars.h / 2.0) / r_vars.near_dist);

	Vec_Clear (r_vars.pos);
	Vec_Clear (r_vars.angles);

	CameraChanged ();
}


void
Setup (uint8_t *buf, int w, int h, int pitch, float fov_x)
{
	r_vars.screen = buf;
	r_vars.w = w;
	r_vars.h = h;
	r_vars.pitch = pitch;

	InitCamera (fov_x);
}


void
CameraRotatePixels (float dx, float dy)
{
	/* using right-handed coordinate system, so positive yaw goes
	 * left across the screen and positive roll goes down */
	r_vars.angles[YAW] += r_vars.fov_x * (-dx / r_vars.w);
	r_vars.angles[PITCH] += r_vars.fov_y * (dy / r_vars.h);

	/* restrict camera angles */
	if (r_vars.angles[PITCH] > M_PI / 2.0)
		r_vars.angles[PITCH] = M_PI / 2.0;
	if (r_vars.angles[PITCH] < -M_PI / 2.0)
		r_vars.angles[PITCH] = -M_PI / 2.0;

	while (r_vars.angles[YAW] >= M_PI * 2.0)
		r_vars.angles[YAW] -= M_PI * 2.0;
	while (r_vars.angles[YAW] < 0.0)
		r_vars.angles[YAW] += M_PI * 2.0;

	CameraChanged ();
}


void
CameraThrust (float left, float up, float forward)
{
	float v[3];

	Vec_Copy (r_vars.left, v);
	Vec_Scale (v, left);
	Vec_Add (r_vars.pos, v, r_vars.pos);

	Vec_Copy (r_vars.up, v);
	Vec_Scale (v, up);
	Vec_Add (r_vars.pos, v, r_vars.pos);

	Vec_Copy (r_vars.forward, v);
	Vec_Scale (v, forward);
	Vec_Add (r_vars.pos, v, r_vars.pos);

	CameraChanged ();
}


void
ClearScreen (void)
{
	int y;

	if (((uintptr_t)r_vars.screen & 0x3) == 0 && (r_vars.w % 4) == 0)
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
DrawWorld (void)
{
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
