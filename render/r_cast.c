#include "cdefs.h"
#include "render.h"
#include "vec.h"

struct surf_s
{
	int plane; // high bit if on back side of plane
	int eplanes[4]; // high bit if on back side of plane
	int color;
	struct surf_s *next_vis;
};

static struct plane_s planes[6] = {
	{ {1, 0, 0}, 0, 0 }, /* west */
	{ {0, 0, 1}, 0, 0 }, /* north */
	{ {1, 0, 0}, 256, 0 }, /* east */
	{ {0, 0, 1}, 64, 0 }, /* south */
	{ {0, 1, 0}, 0, 0 }, /* floor */
	{ {0, 1, 0}, 100, 0 }, /* ceil */
};

#define B 0x80000000
static struct surf_s surfs[6] = {
	{ 0,	{5|B, 3|B, 4, 1}, 1*16+8 },
	{ 1,	{5|B, 0, 4, 2|B}, 3*16+15 },
	{ 2|B,	{5|B, 1, 4, 3|B}, 5*16+15 },
	{ 3|B,	{5|B, 2|B, 4, 0}, 6*16+8 },
	{ 4,	{1, 0, 3|B, 2|B}, 7*16+8 },
	{ 5|B,	{1, 2|B, 3|B, 0}, 11*16+8 },
};

static struct surf_s *vis_surfs;

#if 0
static void
DrawPoint3D (float p[3])
{
	float local[3], v[3];
	float zi;
	int uu, vv;

	Vec_Subtract (p, r_defs.pos, local);
	Vec_Transform (r_defs.xform, local, v);
	if (v[2] > 0.0)
	{
		zi = 1.0 / v[2];
		uu = (int)(r_defs.center_x - r_defs.near_dist * zi * v[0]);
		vv = (int)(r_defs.center_y - r_defs.near_dist * zi * v[1]);
		if (uu >= 0 && uu < r_defs.w && vv >= 0 && vv < r_defs.h)
			r_defs.screen[vv * r_defs.pitch + uu] = 4;
	}
}
#endif


/*
 * NOTES:
 *
 * Use plane types for quick plane side checks
 * When building the map, prefer axis-aligned planes when possible.
 *  Especially true for edge planes, as the plane doesn't have to
 *  be perpindicular to the surface.
 * Can speed up the ray end-point calculations (SIMD)
 * Remember to keep structures aligned for SSE instructions
 * Cast 4+ rays at once. This should work well as the geometry is
 *  fairly large and groups of rays will hit the same surface.
 * If the ray end-point increments results in excessive precision
 *  error we can probably get away with just calculating the endpoint
 *  directly rather than stepping toward it.
 * Probably need to include epsilons in intersection checks.
 * When checking containment, maybe include an epsilon on the back of
 *  the edge plane.
 * Could get crazy and use a BSP-style approach to possibly make
 *  the containment determination faster. The BSP would organize the
 *  surfaces on the leaf plane. Note splits should never be required;
 *  just use planes to binarily find which surface the point is on.
 *  This would get rid of the edge-based containment method. Would be
 *  a bit difficult to build, and must handle non-surface portals.
 *  A "leaf" would be either a surface or a portal. "nodes" would
 *  would similar to the edge plane concept.
 * If using SIMD, maybe build a type of pipelined engine to process
 *  rays at each stage of the casting process.
 * Can probably cache any needed texturing calculation variables each
 *  frame as the surface angles/etc will be constant.
 * Might be able to have the compiler auto-generate our SIMD code by
 *  explicitly using SoA "structs of arrays" rather than AoS.
 */

#if 0
static int
TestHit (const float normal[3], float dist, const float s[3], const float e[3])
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
#endif


#if 0
static void
DrawPoly (void)
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
			/*
			if (y == r_defs.h - 1 && x == 0)
			{
				float z[3];
				z[0] = e[0] - r_defs.far[2][0];
				z[1] = e[1] - r_defs.far[2][1];
				z[2] = e[2] - r_defs.far[2][2];
				printf ("%f %f %f\n", z[0], z[1], z[2]);
			}
			*/
			/*
			if (y == r_defs.h - 1 && x == r_defs.w - 1)
			{
				float z[3];
				z[0] = e[0] - r_defs.far[3][0];
				z[1] = e[1] - r_defs.far[3][1];
				z[2] = e[2] - r_defs.far[3][2];
				printf ("%f %f %f\n", z[0], z[1], z[2]);
			}
			*/

//			if ((x & 3) == 0 || (y & 3) == 0)
//			if ((x & 3) == 0)
			{
				if (TestHit(normal, dist, r_defs.pos, e))
					dest[x] = 4;
			}

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
#endif

#if 0
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
#endif


void
CastRays (void)
{
	int i;
	struct surf_s *s;

	vis_surfs = NULL;

	for (i = 0, s = surfs; i < 6; i++, s++)
	{
	}
}
