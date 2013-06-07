#include <stdint.h>
#include <math.h>
#include <stdlib.h>

#include "bswap.h"
#include "vec.h"
#include "render.h"
#include "r_span.h"
#include "r_edge.h"
#include "r_misc.h"

static void
CameraChanged (void);

struct r_vars_s r_vars;


void
Setup (uint8_t *buf, int w, int h, int pitch, float fov_x)
{
	SwapInit ();

	/* screen buffer */
	r_vars.screen = buf;
	r_vars.w = w;
	r_vars.h = h;
	r_vars.pitch = pitch;

	/* camera */
	r_vars.center_x = r_vars.w / 2.0 + 0.5;
	r_vars.center_y = r_vars.h / 2.0 + 0.5;

	r_vars.fov_x = fov_x;
	r_vars.dist = (r_vars.w / 2.0) / tan(r_vars.fov_x / 2.0);
	r_vars.fov_y = 2.0 * atan((r_vars.h / 2.0) / r_vars.dist);

	Vec_Clear (r_vars.pos);
	Vec_Clear (r_vars.angles);

	CameraChanged ();

	R_SpanSetup ();
	R_EdgeSetup ();

	r_vars.framenum = 0;
}


void
CameraRotatePixels (float screen_dx, float screen_dy)
{
	/* using right-handed coordinate system, so positive yaw goes
	 * left across the screen and positive roll goes down */
	r_vars.angles[YAW] += r_vars.fov_x * (-screen_dx / r_vars.w);
	r_vars.angles[PITCH] += r_vars.fov_y * (screen_dy / r_vars.h);

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


static void
CameraChanged (void)
{
	float cam2world[3][3];
	float v[3];

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

	/* set up view planes */

	adj = 2.0 * (M_PI / 180.0); /* debug: adjust view plane inwards */

	/* left */
	p = &r_vars.vplanes[VPLANE_LEFT];
	ang = (r_vars.fov_x / 2.0) - adj;
	v[0] = -cos (ang);
	v[1] = 0.0;
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);

	/* right */
	p = &r_vars.vplanes[VPLANE_RIGHT];
	ang = (r_vars.fov_x / 2.0) - adj;
	v[0] = cos (ang);
	v[1] = 0.0;
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);

	/* top */
	p = &r_vars.vplanes[VPLANE_TOP];
	ang = (r_vars.fov_y / 2.0) - adj;
	v[0] = 0.0;
	v[1] = -cos (ang);
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);

	/* bottom */
	p = &r_vars.vplanes[VPLANE_BOTTOM];
	ang = (r_vars.fov_y / 2.0) - adj;
	v[0] = 0.0;
	v[1] = cos (ang);
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);
}


#if 1
#include <stdio.h>

static inline int
_ProjectPoint (const float p[3], int *u, int *v)
{
	float local[3], out[3], zi;

	Vec_Subtract (p, r_vars.pos, local);
	Vec_Transform (r_vars.xform, local, out);
	if (out[2] <= 0.0)
	{
		printf("(%g %g %g) -> (%g %g %g)\n",p[0],p[1],p[2],out[0],out[1],out[2]);
		fflush(stdout);
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
	if (*u < 0 || *u >= r_vars.w || *v < 0 || *v >= r_vars.h)
		return 0;

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


static void
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
		if (!_ProjectPoint(verts[clipidx][0], &u1, &v1))
			return;
		if (!_ProjectPoint(verts[clipidx][1], &u2, &v2))
			return;
		DrawLine (u1, v1, u2, v2, c);
	}
}

#endif


static void
DrawGrid (SZ, COLOR)
{
	int i;
	float a[3], b[3];

	for (i = 0; i <= SZ; i += 64)
	{
		/* X-Z plane */
		a[0] = i; a[1] = 0; a[2] = 0;
		b[0] = i; b[1] = 0; b[2] = SZ;
		DrawLine3D (a, b, COLOR);
		a[0] = 0; a[1] = 0; a[2] = i;
		b[0] = SZ; b[1] = 0; b[2] = i;
		DrawLine3D (a, b, COLOR);

		/* X-Y plane */
		a[0] = i; a[1] = 0; a[2] = 0;
		b[0] = i; b[1] = SZ; b[2] = 0;
		DrawLine3D (a, b, COLOR - 4);
		a[0] = 0; a[1] = i; a[2] = 0;
		b[0] = SZ; b[1] = i; b[2] = 0;
		DrawLine3D (a, b, COLOR - 4);

		/* Z-Y plane */
		a[0] = 0; a[1] = 0; a[2] = i;
		b[0] = 0; b[1] = SZ; b[2] = i;
		DrawLine3D (a, b, COLOR - 8);
		a[0] = 0; a[1] = i; a[2] = 0;
		b[0] = 0; b[1] = i; b[2] = SZ;
		DrawLine3D (a, b, COLOR - 4);
	}
}


static float p_verts[4][3] = {
	{0, 72, 0},
	{0, 0, 0},
	{128, 0, 0},
	{128, 72, 0},
};


void
DrawWorld (void)
{
	char spanbuf[0x10000];
	char edgebuf[0x10000];
	int i, ni;

	r_vars.framenum++;

	r_vars.vplanes[0].next = &r_vars.vplanes[1];
	r_vars.vplanes[1].next = &r_vars.vplanes[2];
	r_vars.vplanes[2].next = &r_vars.vplanes[3];
	r_vars.vplanes[3].next = NULL;

	R_BeginSpanFrame (spanbuf, sizeof(spanbuf));
	R_BeginEdgeFrame (edgebuf, sizeof(edgebuf));

	DrawGrid (1024, 16 * 7 - 2);

	for (i = 0; i < sizeof(p_verts) / sizeof(p_verts[0]); i++)
	{
		ni = (i + 1) % (sizeof(p_verts) / sizeof(p_verts[0]));
		DrawLine3D (p_verts[i], p_verts[ni], 16 * 7);
	}

//	R_DrawGSpans ();
}
