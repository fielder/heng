#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>

#include "render.h"
#include "r_edge.h"
#include "vec.h"

// - world
//   begin new frame
//   set up stack spans
//   set up stack edges
//   clear gspans
//  - nodes/leafs/parsing
//    all node or leaf spans must be emitted against gspans before checking portals
//   - poly
//    - edges
//     - sigle edge
//      - run through each active clip plane
//       - ignore edges clipped fully off top/bottom planes


//TODO: would like to associate portals w/ leaves so we can better
// ignore some portals when choosing to draw them on nodes

#define EDGE_FULLY_CLIPPED 0xffffffff
#define EDGE_MAX_REACHED 0x80000000

static struct drawedge_s *r_edges_start = NULL;
static struct drawedge_s *r_edges_end = NULL;
static struct drawedge_s *r_edges = NULL;

/* 2 possible edge starts per screen row */
static struct drawedge_s **r_edge_starts = NULL;

/* when the edge winding leaves the view, crossing a vertical plane,
 * and re-enters to the front side, we must create a new vertical
 * edge */
static int left_clip_count;
static float clip_exit_left[3];
static float clip_enter_left[3];
static int right_clip_count;
static float clip_exit_right[3];
static float clip_enter_right[3];


void
R_EdgeSetup (void)
{
	int sz;

	if (r_edge_starts != NULL)
	{
		free (r_edge_starts);
		r_edge_starts = NULL;
	}

	sz = sizeof(*r_edge_starts) * r_vars.h * 2;
	r_edge_starts = malloc (sz);
	memset (r_edge_starts, 0, sz);
}


void
R_BeginEdgeFrame (void *buf, int buflen)
{
	/* prepare the given edge buffer */
	uintptr_t p = (uintptr_t)buf;

	while ((p % sizeof(struct drawedge_s)) != 0)
	{
		p++;
		buflen--;
	}

	r_edges_start = r_edges = (struct drawedge_s *)p;
	r_edges_end = r_edges_start + (buflen / sizeof(struct drawedge_s));
}


static int
EmitEdge (const float p1[3], const float p2[3])
{
	struct drawedge_s *e;

	float u1_f, v1_f;
	int v1_i;

	float u2_f, v2_f;
	int v2_i;

	float du;

	float local[3], out[3];
	float scale;

	int i;

	if (r_edges == r_edges_end)
		return EDGE_MAX_REACHED;

	Vec_Subtract (p1, r_vars.pos, local);
	Vec_Transform (r_vars.xform, local, out);
	scale = r_vars.dist / out[2];
	u1_f = r_vars.center_x - scale * out[0];
	v1_f = r_vars.center_y - scale * out[1];
	v1_i = floor(v1_f);

	Vec_Subtract (p2, r_vars.pos, local);
	Vec_Transform (r_vars.xform, local, out);
	scale = r_vars.dist / out[2];
	u2_f = r_vars.center_x - scale * out[0];
	v2_f = r_vars.center_y - scale * out[1];
	v2_i = floor(v2_f);

	//TODO: keep y extents on the screen, as we can get the 2 inputs as
	//	vertical edges on the left/right vertical planes
	//	sanity check that it _is_ vertical and on the left/right
	//	that should be the only time we have to clip...

	if (v1_i == v2_i)
	{
		/* cache horizontal edges as fully clipped, as they will
		 * be ignore entirely */
		return EDGE_FULLY_CLIPPED;
	}
	else if (v1_i < v2_i)
	{
		du = (u2_f - u1_f) / (v2_f - v1_f);

		e = r_edges;
		e->u = (u1_f - du * (v1_f - v1_i)) * 0x100000;
		e->du = (du) * 0x100000;
		e->top = v1_i;
		e->bottom = v2_i - 1;
	}
	else
	{
		du = (u1_f - u2_f) / (v1_f - v2_f);

		e = r_edges;
		e->u = (u2_f - du * (v2_f - v2_i)) * 0x100000;
		e->du = (du) * 0x100000;
		e->top = v2_i;
		e->bottom = v1_i - 1;
	}

	i = e->top >> 1;
	if (r_edge_starts[i] == NULL)
	{
		r_edge_starts[i] = e;
	}
	else
	{
		i++;
		if (r_edge_starts[i] != NULL)
		{
			printf ("3+ edge starts on a row\n");
			return EDGE_FULLY_CLIPPED;
		}
		r_edge_starts[i] = e;
	}

	r_edges++;

	return e - r_edges_start;
}


static int
ClipEdge (float p1[3], float p2[3], const struct viewplane_s *planes)
{
	const struct viewplane_s *p;
	float clips[4][3];
	float *clip = clips[0];
	float d1, d2, frac;

	for (p = planes; p != NULL; p = p->next)
	{
		d1 = Vec_Dot (p->normal, p1) - p->dist;
		d2 = Vec_Dot (p->normal, p2) - p->dist;

		if (d1 >= 0.0)
		{
			if (d2 >= 0.0)
			{
				/* both vertices on the front side */
				continue;
			}

			frac = d1 / (d1 - d2);
			clip[0] = p1[0] + frac * (p2[0] - p1[0]);
			clip[1] = p1[1] + frac * (p2[1] - p1[1]);
			clip[2] = p1[2] + frac * (p2[2] - p1[2]);
			p2 = clip;
			clip += 3;

			if (p == &r_vars.vplanes[VPLANE_LEFT])
			{
				clip_exit_left[0] = clip[0];
				clip_exit_left[1] = clip[1];
				clip_exit_left[2] = clip[2];
				left_clip_count++;
			}
			else if (p == &r_vars.vplanes[VPLANE_RIGHT])
			{
				clip_exit_right[0] = clip[0];
				clip_exit_right[1] = clip[1];
				clip_exit_right[2] = clip[2];
				right_clip_count++;
			}
		}
		else
		{
			if (d2 < 0.0)
			{
				/* both vertices behind a plane; the
				 * edge is fully clipped away */
				return EDGE_FULLY_CLIPPED;
			}

			frac = d1 / (d1 - d2);
			clip[0] = p1[0] + frac * (p2[0] - p1[0]);
			clip[1] = p1[1] + frac * (p2[1] - p1[1]);
			clip[2] = p1[2] + frac * (p2[2] - p1[2]);
			p1 = clip;
			clip += 3;

			if (p == &r_vars.vplanes[VPLANE_LEFT])
			{
				clip_enter_left[0] = clip[0];
				clip_enter_left[1] = clip[1];
				clip_enter_left[2] = clip[2];
				left_clip_count++;
			}
			else if (p == &r_vars.vplanes[VPLANE_RIGHT])
			{
				clip_enter_right[0] = clip[0];
				clip_enter_right[1] = clip[1];
				clip_enter_right[2] = clip[2];
				right_clip_count++;
			}
		}
	}

	return EmitEdge (p1, p2);
}


void
R_DrawPoly (struct drawpoly_s *p, const struct viewplane_s *planes)
{
	left_clip_count = 0;
	right_clip_count = 0;

//TODO: ensure we have at least p->num_edges free edges, return if not
//TODO: if an edge clip returns EDGE_MAX_REACHED, return

//TODO: if an edge clip returns EDGE_FULLY_CLIPPED, mark the medge_s cache high bit and set frame num

//TODO: sanity check left/right clip counts
//TODO: after all edges are emitted, emit left & right if clipped off the sides there
}
