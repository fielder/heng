#include <stdint.h>
#include <math.h>
#include <string.h>

#include "bswap.h"
#include "render.h"
#include "vec.h"
#include "map.h"

struct r_vars_s r_vars;


static void
CameraChanged (void)
{
	float cam2world[3][3];
	float v[3];
	float x, y, z, xadj, yadj;
	int i;

	float ang, adj;
	struct viewplane_s *p;

	/* make transformation matrix */
	Vec_Copy (r_vars.angles, v);
	Vec_Scale (v, -1.0);
	Vec_AnglesMatrix (v, r_vars.xform, ROT_MATRIX_ORDER_XYZ);

	/* get view vectors */
	Vec_Copy (r_vars.xform[0], r_vars.left);
	Vec_Copy (r_vars.xform[1], r_vars.up);
	Vec_Copy (r_vars.xform[2], r_vars.forward);

	/* view to world transformation matrix */
	Vec_AnglesMatrix (r_vars.angles, cam2world, ROT_MATRIX_ORDER_ZYX);

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
	for (i = 0; i < 4; i++)
	{
		Vec_Transform (cam2world, r_vars.far[i], v);
		Vec_Add (r_vars.pos, v, r_vars.far[i]);
	}

	/* set up view planes */

	adj = 2.0 * (M_PI / 180.0); /* debug: adjust view plane inwards */

	p = &r_vars.vplanes[VPLANE_LEFT];
	ang = (r_vars.fov_x / 2.0) - adj;
	v[0] = -cos (ang);
	v[1] = 0.0;
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);

	p = &r_vars.vplanes[VPLANE_RIGHT];
	ang = (r_vars.fov_x / 2.0) - adj;
	v[0] = cos (ang);
	v[1] = 0.0;
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);

	p = &r_vars.vplanes[VPLANE_TOP];
	ang = (r_vars.fov_y / 2.0) - adj;
	v[0] = 0.0;
	v[1] = -cos (ang);
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);

	p = &r_vars.vplanes[VPLANE_BOTTOM];
	ang = (r_vars.fov_y / 2.0) - adj;
	v[0] = 0.0;
	v[1] = cos (ang);
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);
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
	SwapInit ();

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


#if 1

static int
_ClipPoint (float p[3])
{
	int i;
	struct viewplane_s *plane;

	for (i = 0, plane = r_vars.vplanes; i < 4; i++, plane++)
	{
		if (Vec_Dot(plane->normal, p) - plane->dist < 0)
			return 0;
	}

	return 1;
}

static inline int
_ProjectPoint (const float p[3], int *u, int *v)
{
	float local[3], out[3], zi;

	Vec_Subtract (p, r_vars.pos, local);
	Vec_Transform (r_vars.xform, local, out);
	if (out[2] <= 0.0)
		return 0;

	zi = 1.0 / out[2];
	*u = r_vars.center_x - r_vars.near_dist * zi * out[0];
	*v = r_vars.center_y - r_vars.near_dist * zi * out[1];

	return 1;
}

static void
DrawPoint3D (float p[3], int c)
{
	if (_ClipPoint(p))
	{
		int u, v;

		if (_ProjectPoint(p, &u, &v))
		{
			if (u >= 0 && u < r_vars.w && v >= 0 && v < r_vars.h)
				r_vars.screen[v * r_vars.pitch + u] = c;
		}
	}
}

static void
DrawLine3D (float p1[3], float p2[3], int c)
{
	if (_ClipPoint(p1) && _ClipPoint(p2))
	{
		int u1, v1, u2, v2;
		if (_ProjectPoint(p1, &u1, &v1) && _ProjectPoint(p2, &u2, &v2))
			DrawLine (u1, v1, u2, v2, c);
	}
}

static void
DrawMapLine2D (const struct line2d_s *l, int c)
{
	float a[3], b[3];

	a[0] = l->v[0]->xy[0];
	a[1] = 0.0;
	a[2] = l->v[0]->xy[1];
	b[0] = l->v[1]->xy[0];
	b[1] = 0.0;
	b[2] = l->v[1]->xy[1];

	DrawLine3D (a, b, c);
}

#endif


void
DrawWorld (void)
{
	int i;
	float xyz[3];

	/*
	for (i = 0; i < map.num_lines_2d; i++)
		DrawMapLine2D (map.lines_2d + i, 16 * 10 + 7);
		*/

	/*
	for (i = 0; i < map.num_verts; i++)
		DrawPoint3D (map.verts[i].xyz, 4);
	*/
	for (i = 0; i < map.num_edges; i++)
		DrawLine3D (map.verts[map.edges[i].v[0]].xyz, map.verts[map.edges[i].v[1]].xyz, 4);

	/*
	for (i = 0; i < map.num_verts_2d; i++)
	{
		xyz[0] = map.verts_2d[i].xy[0];
		xyz[1] = 0.0;
		xyz[2] = map.verts_2d[i].xy[1];
		DrawPoint3D (xyz, 4);
	}
	*/

	xyz[0] = 0; xyz[1] = 0; xyz[2] = 0;
	for (i = 0; i < 64; i++)
	{
		xyz[0] = i * 2;
		DrawPoint3D (xyz, 16 * 11);
	}
	xyz[0] = 0; xyz[1] = 0; xyz[2] = 0;
	for (i = 0; i < 64; i++)
	{
		xyz[1] = i * 2;
		DrawPoint3D (xyz, 16 * 7 + 8);
	}
	xyz[0] = 0; xyz[1] = 0; xyz[2] = 0;
	for (i = 0; i < 64; i++)
	{
		xyz[2] = i * 2;
		DrawPoint3D (xyz, 16 * 12 + 8);
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
