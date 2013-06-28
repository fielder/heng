#include <math.h>
#include <stdint.h>
#include <stdio.h>

#include "cdefs.h"
#include "vec.h"

#include "map.h"
#include "r_defs.h"
#include "render.h"

static struct drawedge_s *r_edges_start = NULL;
static struct drawedge_s *r_edges_end = NULL;
static struct drawedge_s *r_edges = NULL;

static float *r_p1, *r_p2;
static float *r_clip;

static bool r_create_left;
static float r_left_enter[3];
static float r_left_exit[3];

static bool r_create_right;
static float r_right_enter[3];
static float r_right_exit[3];


void
E_EdgeSetup (void)
{
}


void
E_BeginEdgeFrame (void *buf, int buflen)
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


static struct drawedge_s *
EmitNewEdge (void)
{
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

//TODO: adjust and floor the final u, to properly match up which
//	pixel center the span will cover?

	if (v1_i == v2_i)
	{
		return NULL;
	}
	else if (v1_i < v2_i)
	{
		du = (u2_f - u1_f) / (v2_f - v1_f);
		r_edges->u = (u1_f + du * (v1_i + 0.5 - v1_f)) * 0x100000;
		r_edges->du = (du) * 0x100000;
		r_edges->top = v1_i;
		r_edges->bottom = v2_i - 1;
		r_edges->is_right = 0;
		r_edges++;
	}
	else
	{
		du = (u1_f - u2_f) / (v1_f - v2_f);
		r_edges->u = (u2_f + du * (v2_i + 0.5 - v2_f)) * 0x100000;
		r_edges->du = (du) * 0x100000;
		r_edges->top = v2_i;
		r_edges->bottom = v1_i - 1;
		r_edges->is_right = 1;
		r_edges++;
	}

	return r_edges - 1;
}


static inline void
EmitCached (const struct drawedge_s *cached)
{
	r_edges->owner		= cached->owner;
	r_edges->top		= cached->top;
	r_edges->bottom		= cached->bottom;
	r_edges->u		= cached->u;
	r_edges->du		= cached->du;
	r_edges->is_right	= cached->is_right;
	r_edges++;
}


static int
ClipTopBottom (const struct viewplane_s *cplanes)
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
				r_clip[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
				r_clip[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
				r_clip[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

				r_p2 = r_clip;
				r_clip += 3;
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
				r_clip[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
				r_clip[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
				r_clip[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

				r_p1 = r_clip;
				r_clip += 3;
			}
		}
	}

	return 1;
}


#define FRONT(dist) ((dist) >= 0.0)

static int
ClipLeftRight (	struct viewplane_s *left,
		struct viewplane_s *right)
{
	float *isect_l, *isect_r;
	float d1_l = 1.0, d2_l = 1.0;
	float d1_r = 1.0, d2_r = 1.0;
	float frac;
	int s1_l, s2_l;
	int s1_r, s2_r;
	int all;

	if (left != NULL)
	{
		d1_l = Vec_Dot(left->normal, r_p1) - left->dist;
		d2_l = Vec_Dot(left->normal, r_p2) - left->dist;
	}

	if (right != NULL)
	{
		d1_r = Vec_Dot(right->normal, r_p1) - right->dist;
		d2_r = Vec_Dot(right->normal, r_p2) - right->dist;
	}

	s1_l = FRONT(d1_l);
	s2_l = FRONT(d2_l);
	s1_r = FRONT(d1_r);
	s2_r = FRONT(d2_r);

	all = (s1_l << 0) | (s2_l << 1) | (s1_r << 2) | (s2_r << 3);

	/* all in front unclipped */
	if (all == 0xf)
		return 1;
	/* behind a plane and unclipped */
	if (all == 0x0 || all == 0x3 || all == 0xc)
		return 0;

	/* crosses the left plane */
	if (s1_l ^ s2_l)
	{
		if (s1_l) /* front -> back */
		{
			isect_l = r_left_exit;
			r_create_left = true;

			frac = d1_l / (d1_l - d2_l);
			isect_l[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
			isect_l[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
			isect_l[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

			if ((s1_r | s2_r) == 0x0)
			{
				/* cut by the left plane, but all behind the right
				 * all we did was update r_left_exit */
				return 0;
			}
			else if (s1_r & s2_r)
			{
				/* cut by the left plane, but all in front of the
				 * right plane */
				r_p2 = isect_l;
				return 1;
			}
		}
		else /* back -> front */
		{
			isect_l = r_left_enter;
			r_create_left = true;

			frac = d1_l / (d1_l - d2_l);
			isect_l[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
			isect_l[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
			isect_l[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

			if ((s1_r | s2_r) == 0x0)
			{
				/* cut by the left plane, but all behind the right
				 * all we did was update r_left_enter */
				return 0;
			}
			else if (s1_r & s2_r)
			{
				/* cut by the left plane, but all in front of the
				 * right plane */
				r_p1 = isect_l;
				return 1;
			}
		}
	}

	/* crosses the right plane */
	if (s1_r ^ s2_r)
	{
		if (s1_r) /* front -> back */
		{
			isect_r = r_right_exit;
			r_create_right = true;

			frac = d1_r / (d1_r - d2_r);
			isect_r[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
			isect_r[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
			isect_r[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

			if ((s1_l | s2_l) == 0x0)
			{
				/* cut by the right plane, but all behind the left
				 * all we did was update r_right_exit */
				return 0;
			}
			else if (s1_l & s2_l)
			{
				/* cut by the right plane, but all in front of the
				 * left plane */
				r_p2 = isect_r;
				return 1;
			}
		}
		else /* back -> front */
		{
			isect_r = r_right_enter;
			r_create_right = true;

			frac = d1_r / (d1_r - d2_r);
			isect_r[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
			isect_r[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
			isect_r[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

			if ((s1_l | s2_l) == 0x0)
			{
				/* cut by the right plane, but all behind the left
				 * all we did was update r_right_enter */
				return 0;
			}
			else if (s1_l & s2_l)
			{
				/* cut by the right plane, but all in front of the
				 * left plane */
				r_p1 = isect_r;
				return 1;
			}
		}
	}

	if (all == 0xa)
	{
		/* edge starts off behind both planes (behind the
		 * viewpoint), and ends in front of both planes */
		if (FRONT(Vec_Dot(left->normal, r_right_enter) - left->dist))
			r_p1 = r_right_enter;
		else
			r_p1 = r_left_enter;
	}
	else if (all == 0x5)
	{
		/* edge starts off in front of both planes and ends
		 * behind both planes (behind the veiwpoint) */
		if (FRONT(Vec_Dot(left->normal, r_right_exit) - left->dist))
			r_p2 = r_right_exit;
		else
			r_p2 = r_left_exit;
	}
	else if (all == 0x6)
	{
		/* edge runs from left-to-right across both planes */
		if (FRONT(Vec_Dot(left->normal, r_right_exit) - left->dist))
		{
			r_p1 = r_left_enter;
			r_p2 = r_right_exit;
		}
		else
			return 0;
	}
	else if (all == 0x9)
	{
		/* edge runs from right-to-left across both planes */
		if (FRONT(Vec_Dot(left->normal, r_right_enter) - left->dist))
		{
			r_p1 = r_right_enter;
			r_p2 = r_left_exit;
		}
		else
			return 0;
	}

	return 1;
}

#undef FRONT


int
E_GenEdges (	const unsigned short *edgerefs,
		int num_edges,
		struct viewplane_s *leftright[2],
		struct viewplane_s *topbottom,
		struct drawedge_s *out[2])
{
	float clipverts[4 * 3];
	struct medge_s *medge;
	struct drawedge_s *emit_start;
	unsigned short eref;
#if 0
	struct drawedge_s *emit;
#endif
#if 0
	unsigned int cache_idx;
	int e_lr_flags;
#endif

	if (r_edges + num_edges + 2 > r_edges_end)
	{
		//TODO: reset the pipeline and continue
		return 0;
	}

	emit_start = r_edges;
	r_create_left = false;
	r_create_right = false;

	while (num_edges--)
	{
		eref = *edgerefs++;
		medge = &map.edges[eref & 0x7fff];
#if 0
		cache_idx = medge->cache_index & 0x7fffffff;

		if ((medge->cache_index & 0x80000000) && cache_idx == r_vars.framenum)
		{
			/* edge is marked as non-visible, ignore */
		}
		else if (cache_idx < (r_edges - r_edges_start) &&
			r_edges_start[cache_idx].owner == medge)
		{
			/* cached edge */
			EmitCached (&r_edges_start[cache_idx]);
		}
		else
#endif
		{
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
			r_clip = clipverts;

#if 1
			if (leftright[0] != NULL || leftright[1] != NULL)
			{
				if (!ClipLeftRight(leftright[0], leftright[1]))
					continue;
			}

			if (ClipTopBottom(topbottom))
				EmitNewEdge ();
#endif

#if 0
			if (!ClipLeftRight(cplanes[0], &e_lr_flags))
			{
				/* Edges fully off the left/right aren't used.
				 * Not used even to generate enter/exit points
				 * as we avoid projecting points that lie behind
				 * the viewpoint */
				medge->cache_index = 0x80000000 | r_vars.framenum;
			}
			else
			{
				if (ClipTopBottom(cplanes[1]))
				{
					if ((emit = EmitNewEdge()) != NULL)
					{
						emit->owner = medge;
						medge->cache_index = emit - r_edges_start;
					}
					else
					{
						/* ignore horizontal edges entirely as they never
						 * contribute to span generation at all */
						if (e_lr_flags == 0x0)
							medge->cache_index = 0x80000000 | r_vars.framenum;
					}
				}
				else
				{
					/* cache edges off the top/bottom as fully rejected, but
					 * only if it doesn't contribute to enter/exit points */
					if (e_lr_flags == 0x0)
						medge->cache_index = 0x80000000 | r_vars.framenum;
				}
			}
#endif
		}
	}

	if (r_create_left)
	{
		r_p1 = r_left_exit;
		r_p2 = r_left_enter;
		r_clip = clipverts;
		if (ClipTopBottom(topbottom))
			EmitNewEdge ();
	}

	if (r_create_right)
	{
		r_p1 = r_right_exit;
		r_p2 = r_right_enter;
		r_clip = clipverts;
		if (ClipTopBottom(topbottom))
			EmitNewEdge ();
	}

	/* no edges emitted */
	if (emit_start == r_edges)
		return 0;

	/* now put the new edges into left/right lists, both sorted
	 * by the top screen coordinate of the edge */
	{
		struct drawedge_s head[2];
		struct drawedge_s *last[2];
		struct drawedge_s *prev;
		struct drawedge_s *e;

		head[0].top = -99999;
		head[0].next = NULL;
		last[0] = &head[0];

		head[1].top = -99999;
		head[1].next = NULL;
		last[1] = &head[1];

		for (e = emit_start; e != r_edges; e++)
		{
			if (e->top >= last[e->is_right]->top)
			{
				e->next = NULL;
				last[e->is_right]->next = e;
				last[e->is_right] = e;
			}
			else
			{
				for (	prev = &head[e->is_right];
					/* Note we're not doing an end-of-list NULL
					 * check here. That case should be caught by
					 * the last check above, meaning we will
					 * never hit the end of the list here. */
					prev->next->top < e->top;
					prev = prev->next) {}
				e->next = prev->next;
				prev->next = e;
			}
		}

		out[0] = head[0].next;
		out[1] = head[1].next;
	}

	return 1;
}


#if 0

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

#endif


#if 0
			if (!ClipEdge(clipverts, cplanes))
			{
				/* any edge off the screen can be ignored */
				medge->cache_index = 0x80000000 | r_vars.framenum;
			}
			else
			{
				if ((emit = EmitNewEdge()) != NULL)
				{
					emit->owner = medge;
					medge->cache_index = emit - r_edges_start;
				}
				else
				{
					/* ignore horizontal edges entirely as
					 * they never contribute to span
					 * generation at all */
					medge->cache_index = 0x80000000 | r_vars.framenum;
				}
			}
#endif


#if 0
//TODO: Never cache an edge clipped off the left/right and passed onto
//	the next clipping stage.
//	The next time around the enter/exit points need to be recalced.

static int
ClipLeftRight (const struct viewplane_s *cplanes, int *flags)
{
	float d1, d2, frac;
	int newflags = 0x0;

	*flags = 0x0;

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
				r_clip[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
				r_clip[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
				r_clip[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

				if (cplanes == &r_vars.vplanes[VPLANE_LEFT])
				{
					/* left exit */
					r_left_exit[0] = r_clip[0];
					r_left_exit[1] = r_clip[1];
					r_left_exit[2] = r_clip[2];
					newflags |= CLIP_LEFT_EXIT;
				}
				else
				{
					/* right exit */
					r_right_exit[0] = r_clip[0];
					r_right_exit[1] = r_clip[1];
					r_right_exit[2] = r_clip[2];
					newflags |= CLIP_RIGHT_EXIT;
				}

				r_p2 = r_clip;
				r_clip += 3;
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
				/* Note we return without updating the
				 * global left/right clip flags */
				return 0;
			}
			else
			{
				/* edge runs from back -> front */

				frac = d1 / (d1 - d2);
				r_clip[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
				r_clip[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
				r_clip[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

				if (cplanes == &r_vars.vplanes[VPLANE_LEFT])
				{
					/* left enter */
					r_left_enter[0] = r_clip[0];
					r_left_enter[1] = r_clip[1];
					r_left_enter[2] = r_clip[2];
					newflags |= CLIP_LEFT_ENTER;
				}
				else
				{
					/* right enter */
					r_right_enter[0] = r_clip[0];
					r_right_enter[1] = r_clip[1];
					r_right_enter[2] = r_clip[2];
					newflags |= CLIP_RIGHT_ENTER;
				}

				r_p1 = r_clip;
				r_clip += 3;
			}
		}
	}

//TODO handle the case where we clip against both planes, but in teh same direction

	*flags = newflags;
	r_clipflags |= newflags;

	return 1;
}
#endif


#if 0
static int
ClipTopBottom (const struct viewplane_s *plane)
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
				r_clip[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
				r_clip[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
				r_clip[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

				r_p2 = r_clip;
				r_clip += 3;
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
				r_clip[0] = r_p1[0] + frac * (r_p2[0] - r_p1[0]);
				r_clip[1] = r_p1[1] + frac * (r_p2[1] - r_p1[1]);
				r_clip[2] = r_p1[2] + frac * (r_p2[2] - r_p1[2]);

				r_p1 = r_clip;
				r_clip += 3;
			}
		}
	}

	return 1;
}
#endif
