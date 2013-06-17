#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>

#include "cdefs.h"
#include "vec.h"

#include "map.h"
#include "render.h"
#include "r_defs.h"
#include "r_edge.h"

//TODO: need to emit edges for left/right clips

//FIXME: it's important to clip against the left/right planes first
//	so to generate the enter/exit points properly, else for the
//	case of a poly entirely surrounding the view, if we tested
//	top/bottom first, all edges woud be clipped away leaving
//	nothing enter/exit points and therefore nothing visible
//	do it another way...?

//FIXME: need to fix the filly clipped edge caching
//	eg: If a poly isn't visible at all, and an edge that is clipped
//	off the left/right, then fully rejected as above/below the frustum,
//	we will cache it as entirely clipped. If a visible poly shares that
//	edge we'll skip it when iterating over edges.
//	Basically, we can't cache an edge as fully clipped if it is clipped
//	by the left/right, then fully rejected off the top/bottom. A fully
//	rejected edge must not touch the left/right planes.

//TODO: would like to associate portals w/ leaves so we can better
// ignore some portals when choosing to draw them on nodes

#define EDGE_FULLY_CLIPPED 0xffffffff
#define EDGE_MAX_REACHED 0x80000000

static struct drawedge_s *r_edges_start = NULL;
static struct drawedge_s *r_edges_end = NULL;
static struct drawedge_s *r_edges = NULL;

static struct drawedge_s sort_head;
static struct drawedge_s *sort_last;

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


static void
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

	if (r_edges == r_edges_end)
		return;

	Vec_Subtract (p1, r_vars.pos, local);
	Vec_Transform (r_vars.xform, local, out);
	scale = r_vars.dist / out[2];
	u1_f = r_vars.center_x - scale * out[0];
	v1_f = r_vars.center_y - scale * out[1];
	v1_i = floor(v1_f + 0.5);

	Vec_Subtract (p2, r_vars.pos, local);
	Vec_Transform (r_vars.xform, local, out);
	scale = r_vars.dist / out[2];
	u2_f = r_vars.center_x - scale * out[0];
	v2_f = r_vars.center_y - scale * out[1];
	v2_i = floor(v2_f + 0.5);

	//TODO: keep y extents on the screen, as we can get the 2 inputs as
	//	vertical edges on the left/right vertical planes
	//	sanity check that it _is_ vertical and on the left/right
	//	that should be the only time we have to clip...

	if (v1_i == v2_i)
	{
		/* cache horizontal edges as fully clipped, as they will
		 * be ignore entirely */
		return;
	}
	else if (v1_i < v2_i)
	{
		e = r_edges;
		r_edges++;

		du = (u2_f - u1_f) / (v2_f - v1_f);
		e->u = (u1_f + du * (v1_i + 0.5 - v1_f)) * 0x100000;
		e->du = (du) * 0x100000;
		e->top = v1_i;
		e->bottom = v2_i - 1;
	}
	else
	{
		e = r_edges;
		r_edges++;

		du = (u1_f - u2_f) / (v1_f - v2_f);
		e->u = (u2_f + du * (v2_i + 0.5 - v2_f)) * 0x100000;
		e->du = (du) * 0x100000;
		e->top = v2_i;
		e->bottom = v1_i - 1;
	}

	if (e->top >= sort_last->top)
	{
		e->next = NULL;
		sort_last->next = e;
		sort_last = e;
	}
	else
	{
		struct drawedge_s *prev;
		for (	prev = &sort_head;
			prev->next != NULL && prev->next->top < e->top;
			prev = prev->next) {}
		e->next = prev->next;
		prev->next = e;
	}
}


static void
ClipEdge (float p1[3], float p2[3], const struct viewplane_s *planes)
{
	float clips[4 * 3];
	float *clip = clips;
	float d1, d2, frac;

	for (; planes != NULL; planes = planes->next)
	{
		d1 = Vec_Dot (planes->normal, p1) - planes->dist;
		d2 = Vec_Dot (planes->normal, p2) - planes->dist;

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

			if (planes == &r_vars.vplanes[VPLANE_LEFT])
			{
				clip_exit_left[0] = clip[0];
				clip_exit_left[1] = clip[1];
				clip_exit_left[2] = clip[2];
				left_clip_count++;
			}
			else if (planes == &r_vars.vplanes[VPLANE_RIGHT])
			{
				clip_exit_right[0] = clip[0];
				clip_exit_right[1] = clip[1];
				clip_exit_right[2] = clip[2];
				right_clip_count++;
			}

			p2 = clip;
			clip += 3;
		}
		else
		{
			if (d2 < 0.0)
			{
				/* both vertices behind a plane; the
				 * edge is fully clipped away */
				return;
			}

			frac = d1 / (d1 - d2);
			clip[0] = p1[0] + frac * (p2[0] - p1[0]);
			clip[1] = p1[1] + frac * (p2[1] - p1[1]);
			clip[2] = p1[2] + frac * (p2[2] - p1[2]);

			if (planes == &r_vars.vplanes[VPLANE_LEFT])
			{
				clip_enter_left[0] = clip[0];
				clip_enter_left[1] = clip[1];
				clip_enter_left[2] = clip[2];
				left_clip_count++;
			}
			else if (planes == &r_vars.vplanes[VPLANE_RIGHT])
			{
				clip_enter_right[0] = clip[0];
				clip_enter_right[1] = clip[1];
				clip_enter_right[2] = clip[2];
				right_clip_count++;
			}

			p1 = clip;
			clip += 3;
		}
	}

	EmitEdge (p1, p2);
}


struct drawedge_s *
R_GenEdges (const unsigned short *edgerefs, int num_edges, struct viewplane_s *cplanes)
{
	unsigned short eref;
	struct medge_s *medge;
	struct mvertex_s *v1, *v2;

	sort_head.top = -99999;
	sort_head.next = NULL;
	sort_last = &sort_head;

	while (num_edges--)
	{
		eref = *edgerefs++;

		medge = &map.edges[eref & 0x7fff];

		if ((eref & 0x8000) == 0x8000)
		{
			v1 = map.verts + medge->v[1];
			v2 = map.verts + medge->v[0];
		}
		else
		{
			v1 = map.verts + medge->v[0];
			v2 = map.verts + medge->v[1];
		}

		ClipEdge (v1->xyz, v2->xyz, cplanes);
	}

	return sort_head.next;
}


#if 0


static void
DrawEdge (struct drawedge_s *e)
{
	int u, y;

	u = e->u;
	y = e->top;
	while (y <= e->bottom)
	{
		r_vars.screen[y * r_vars.pitch + (u >> 20)] = 16 * 7;
		y += 1;
		u += e->du;
	}
}

void
R_DrawPoly (const struct viewplane_s *planes)
{
	int i, ni;

	if (r_vars.pos[2] < p_verts[0][2] + 0.01)
		return;

	left_clip_count = 0;
	right_clip_count = 0;

	for (i = 0; i < sizeof(p_verts) / sizeof(p_verts[0]); i++)
	{
		ni = (i + 1) % (sizeof(p_verts) / sizeof(p_verts[0]));
		ClipEdge (p_verts[i], p_verts[ni], planes);
	}

	if (left_clip_count && left_clip_count != 2)
	{
		printf ("bad left count: %d\n", left_clip_count);
	}
	if (right_clip_count && right_clip_count != 2)
	{
		printf ("bad right count: %d\n", right_clip_count);
	}
	struct drawedge_s *e;
	for (e = r_edges_start; e != r_edges; e++)
		DrawEdge (e);

//TODO: ensure we have at least p->num_edges free edges, return if not
//TODO: if an edge clip returns EDGE_MAX_REACHED, return
//TODO: sanity check left/right clip counts
//TODO: after all edges are emitted, emit left & right if clipped off the sides there
}

#endif
