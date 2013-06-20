#include <stdint.h>
#include <math.h>

#include "cdefs.h"
#include "bswap.h"
#include "vec.h"

#include "render.h"
#include "r_span.h"
#include "r_edge.h"
#include "r_bsp.h"

struct r_vars_s r_vars;

static bool cam_changed = false;


static void
CalcCamera (void);


void
R_SetupBuffer (uint8_t *buf, int w, int h, int pitch)
{
	SwapInit ();

	r_vars.screen = buf;
	r_vars.w = w;
	r_vars.h = h;
	r_vars.pitch = pitch;

	r_vars.framenum = 0;

	R_SpanSetup ();
	R_EdgeSetup ();
}


void
R_SetupProjection (float fov_x)
{
	r_vars.center_x = r_vars.w / 2.0;
	r_vars.center_y = r_vars.h / 2.0;

	r_vars.fov_x = fov_x;
	r_vars.dist = (r_vars.w / 2.0) / tan(r_vars.fov_x / 2.0);
	r_vars.fov_y = 2.0 * atan((r_vars.h / 2.0) / r_vars.dist);

	Vec_Clear (r_vars.pos);
	Vec_Clear (r_vars.angles);

	CalcCamera ();
}


void
R_SetCamera (float pos[3], float angles[3])
{
	Vec_Copy (pos, r_vars.pos);
	Vec_Copy (angles, r_vars.angles);
	cam_changed = true;
}


static void
CalcCamera (void)
{
	float cam2world[3][3];
	float v[3];
	float ang;
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

/* debug: adjust view plane inwards */
#define ADJ (2.0 * (M_PI / 180.0))

	/* left */
	p = &r_vars.vplanes[VPLANE_LEFT];
	ang = (r_vars.fov_x / 2.0) - ADJ;
	v[0] = -cos (ang);
	v[1] = 0.0;
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);

	/* right */
	p = &r_vars.vplanes[VPLANE_RIGHT];
	ang = (r_vars.fov_x / 2.0) - ADJ;
	v[0] = cos (ang);
	v[1] = 0.0;
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);

	/* top */
	p = &r_vars.vplanes[VPLANE_TOP];
	ang = (r_vars.fov_y / 2.0) - ADJ;
	v[0] = 0.0;
	v[1] = -cos (ang);
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);

	/* bottom */
	p = &r_vars.vplanes[VPLANE_BOTTOM];
	ang = (r_vars.fov_y / 2.0) - ADJ;
	v[0] = 0.0;
	v[1] = cos (ang);
	v[2] = sin (ang);
	Vec_Transform (cam2world, v, p->normal);
	p->dist = Vec_Dot (p->normal, r_vars.pos);
}


void
R_SetDebug (int debug)
{
	r_vars.debug = debug;
}


void
R_Refresh (void)
{
	if (cam_changed)
	{
		CalcCamera ();
		cam_changed = false;
	}

	r_vars.framenum++;

	R_DrawWorld ();
}
