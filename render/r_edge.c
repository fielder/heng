#include <math.h>
#include <stdint.h>
#include <stdio.h>

#include "cdefs.h"
#include "vec.h"

#include "map.h"
#include "render.h"
#include "r_defs.h"
#include "r_edge.h"

//TODO: would like to associate portals w/ leaves so we can better
// ignore some portals when choosing to draw them on nodes

static struct drawedge_s *r_edges_start = NULL;
static struct drawedge_s *r_edges_end = NULL;
static struct drawedge_s *r_edges = NULL;

static struct drawedge_s sort_head[2];
static struct drawedge_s *sort_last[2];

static float *r_p1, *r_p2;


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
SortIn (struct drawedge_s *e)
{
	if (e->top >= sort_last[e->is_right]->top)
	{
		e->next = NULL;
		sort_last[e->is_right]->next = e;
		sort_last[e->is_right] = e;
	}
	else
	{
		struct drawedge_s *prev;
		for (	prev = &sort_head[e->is_right];
			/* Note we're not doing an end-of-list NULL
			 * check here. That case should be caught by
			 * the sort_last check above, meaning we will
			 * never hit the end of the list here. */
			prev->next->top < e->top;
			prev = prev->next) {}
		e->next = prev->next;
		prev->next = e;
	}
}


static struct drawedge_s *
EmitNewEdge (void)
{
	struct drawedge_s *e;

	float u1_f, v1_f;
	int v1_i;

	float u2_f, v2_f;
	int v2_i;

	float du;

	float local[3], out[3];
	float scale;

	Vec_Subtract (r_p1, r_vars.pos, local);
	Vec_Transform (r_vars.xform, local, out);
	scale = r_vars.dist / out[2];
	u1_f = r_vars.center_x - scale * out[0];
	v1_f = r_vars.center_y - scale * out[1];
	v1_i = floor(v1_f + 0.5);

	Vec_Subtract (r_p2, r_vars.pos, local);
	Vec_Transform (r_vars.xform, local, out);
	scale = r_vars.dist / out[2];
	u2_f = r_vars.center_x - scale * out[0];
	v2_f = r_vars.center_y - scale * out[1];
	v2_i = floor(v2_f + 0.5);

	if (v1_i == v2_i)
	{
		/* horizontal edges should be cached like fully rejected
		 * edges */
		return NULL;
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
		e->is_right = 0;
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
		e->is_right = 1;
	}

	SortIn (e);

	return e;
}


static int
ClipEdge (float *clip, const struct viewplane_s *cplanes)
{
	float d1, d2, frac;

	for (; cplanes != NULL; cplanes = cplanes->next)
	{
		d1 = Vec_Dot (cplanes->normal, r_p1) - cplanes->dist;
		d2 = Vec_Dot (cplanes->normal, r_p2) - cplanes->dist;

		if (d1 >= 0.0)
		{
			if (d2 < 0.0)
			{
				/* edge runs from front -> back */

				frac = d1 / (d1 - d2);
				clip[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
				clip[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
				clip[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

				r_p2 = clip;
				clip += 3;
			}
			else
			{
				/* both vertices on the front side */
			}
		}
		else
		{
			if (d2 < 0.0)
			{
				/* both vertices behind a plane; the
				 * edge is fully clipped away */
				return 0;
			}
			else
			{
				/* edge runs from back -> front */

				frac = d1 / (d1 - d2);
				clip[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
				clip[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
				clip[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

				r_p1 = clip;
				clip += 3;
			}
		}
	}

	return 1;
}


static void
EmitCached (const struct drawedge_s *cached)
{
	struct drawedge_s *e = r_edges++;

	e->owner	= cached->owner;
	e->top		= cached->top;
	e->bottom	= cached->bottom;
	e->u		= cached->u;
	e->du		= cached->du;
	e->is_right	= cached->is_right;

	SortIn (e);
}


int
R_GenEdges (const unsigned short *edgerefs, int num_edges, const struct viewplane_s *cplanes, struct drawedge_s *out[2])
{
	float clipverts[4 * 3];
	struct medge_s *medge;
	struct drawedge_s *first_emit, *emit;
	unsigned short eref;
	unsigned int cache_idx;

	if (r_edges + num_edges + 2 > r_edges_end)
	{
		//TODO: reset the pipeline and continue
		return 0;
	}

	first_emit = r_edges;

	sort_head[0].top = -99999;
	sort_head[0].next = NULL;
	sort_last[0] = &sort_head[0];

	sort_head[1].top = -99999;
	sort_head[1].next = NULL;
	sort_last[1] = &sort_head[1];

	while (num_edges--)
	{
		eref = *edgerefs++;
		medge = &map.edges[eref & 0x7fff];
		cache_idx = medge->cache_index & 0x7fffffff;

		if ((medge->cache_index & 0x80000000) && cache_idx == r_vars.framenum)
		{
			/* edge is marked as non-visible, ignore */
			/* or horizontal */
		}
		else if (cache_idx < (r_edges - r_edges_start) &&
			r_edges_start[cache_idx].owner == medge)
		{
			/* cached edge */
			EmitCached (&r_edges_start[cache_idx]);
		}
		else
		{
			//TODO: probably can complety get rid of
			// edge directions if we don't care about
			// knowing which poly is on the left/right
			// of an emitted edge; that's really only
			// needed for Quake's edge sorting/scanning
			if ((eref & 0x8000) == 0x8000)
			{
				r_p1 = map.verts[medge->v[1]].xyz;
				r_p2 = map.verts[medge->v[0]].xyz;
			}
			else
			{
				r_p1 = map.verts[medge->v[0]].xyz;
				r_p2 = map.verts[medge->v[1]].xyz;
			}

			if (!ClipEdge(clipverts, cplanes))
			{
				/* any edge off the screen can be ignored */
				medge->cache_index = 0x80000000 | r_vars.framenum;
			}
			else
			{
				if ((emit = EmitNewEdge()) == NULL)
				{
					/* ignore horizontal edges entirely as
					 * they never contribute to span
					 * generation at all */
					medge->cache_index = 0x80000000 | r_vars.framenum;
				}
				else
				{
					emit->owner = medge;
					medge->cache_index = emit - r_edges_start;
				}
			}
		}
	}

	/* no edges emitted */
	if (first_emit == r_edges)
		return 0;

	//TODO: postpone edge y-sorting to here
	// simply run through first_emit to r_edges, sort into out lists

	out[0] = sort_head[0].next;
	out[1] = sort_head[1].next;

	return 1;
}
