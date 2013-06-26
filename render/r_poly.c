#include <string.h>
#include <stdint.h>

#include "cdefs.h"

#include "r_defs.h"
#include "render.h"

static void
R_RenderPolySpans (struct drawpoly_s *p);


struct drawpoly_s *r_polys = NULL;
static struct drawpoly_s *r_polys_start = NULL;
static struct drawpoly_s *r_polys_end = NULL;


void
R_BeginPolyFrame (void *buf, int buflen)
{
	/* prepare the given poly buffer */
	uintptr_t p = (uintptr_t)buf;

	while ((p % sizeof(struct drawpoly_s)) != 0)
	{
		p++;
		buflen--;
	}

	r_polys_start = r_polys = (struct drawpoly_s *)p;
	r_polys_end = r_polys_start + (buflen / sizeof(struct drawpoly_s));
}


void
R_PolyGenEdges (struct mpoly_s *poly, const struct viewplane_s *cplanes)
{
	struct drawedge_s *edges[2];

	if (r_polys == r_polys_end)
		return; //TODO: flush the pipeline and continue on

	if (R_GenEdges(poly->edges, poly->num_edges, cplanes, edges))
	{
		struct drawpoly_s *p = r_polys++;

		p->edges[0] = edges[0];
		p->edges[1] = edges[1];
		p->mpoly = poly;
		p->spans = NULL;
		p->num_spans = 0;
	}
}


//TODO: always check for negative-len span before emitting
void
R_ScanPolyEdges (struct drawpoly_s *p)
{
	struct drawedge_s *left, *right;
	int v;
	int l_u, l_du, l_next_v;
	int r_u, r_du, r_next_v;
	int next_v;

	/* shut up compiler */
	l_u = 0;
	l_du = 0;
	r_u = 0;
	r_du = 0;

	p->spans = r_spans;

	left = p->edges[0];
	right = p->edges[1];

	v = 99999;
	if (left != NULL && left->top < v)
		v = left->top;
	if (right != NULL && right->top < v)
		v = right->top;

	l_next_v = v;
	r_next_v = v;

	while (left != NULL || right != NULL)
	{
		if (v == l_next_v)
		{
			if (left == NULL)
			{
				l_u = 0;
				l_du = 0;
				l_next_v = r_vars.h;
			}
			else
			{
				if (left->top == v)
				{
					l_u = left->u;
					l_du = left->du;
					l_next_v = left->bottom + 1;
					left = left->next;
				}
				else
				{
					l_u = 0;
					l_du = 0;
					l_next_v = left->top;
				}
			}
		}

		if (v == r_next_v)
		{
			if (right == NULL)
			{
				r_u = (r_vars.w - 1) << 20;
				r_du = 0;
				r_next_v = r_vars.h;
			}
			else
			{
				if (right->top == v)
				{
					r_u = right->u;
					r_du = right->du;
					r_next_v = right->bottom + 1;
					right = right->next;
				}
				else
				{
					r_u = (r_vars.w - 1) << 20;
					r_du = 0;
					r_next_v = right->top;
				}
			}
		}

		next_v = (l_next_v < r_next_v) ? l_next_v : r_next_v;

		while (v < next_v)
		{
			if (r_u > l_u)
				R_ClipAndEmitSpan (v, l_u >> 20, r_u >> 20);
			l_u += l_du;
			r_u += r_du;
			v++;
		}
	}

	p->num_spans = r_spans - p->spans;
}


void
R_RenderPolys (void)
{
	struct drawpoly_s *p;

	for (p = r_polys_start; p != r_polys; p++)
		R_RenderPolySpans (p);
}


static void
R_RenderPolySpans (struct drawpoly_s *p)
{
	struct drawspan_s *span;
	int i, color;

	if (!p->num_spans)
		return;

	//TODO: texture mapping magic here

	color = ((uintptr_t)p->mpoly >> 2) & 0xff;
color = 16 * 7;//DEBUG
color = 251;//DEBUG

	for (i = 0, span = p->spans; i < p->num_spans; i++, span++)
	{
		memset (r_vars.screen + span->v * r_vars.pitch + span->u,
			color,
			span->len);
	}
}
