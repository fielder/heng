#include <string.h>
#include <stdint.h>

#include "cdefs.h"

#include "render.h"
#include "r_defs.h"
#include "r_span.h"
#include "r_edge.h"
#include "r_poly.h"

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
#if 1
	struct drawedge_s *left_next, *right_next;
	int v, next_v;
	int u_l, u_step_l;
	int u_r, u_step_r;

	p->spans = r_spans;

	left_next = p->edges[0];
	right_next = p->edges[1];

	v = 99999;
	if (left_next != NULL && left_next->top < v)
		v = left_next->top;
	if (right_next != NULL && right_next->top < v)
		v = right_next->top;

//	while (left_next != NULL || right_next != NULL)
//	{
//	}

#endif

#if 0
	int u, v;
	struct drawedge_s *e;

	p->spans = r_spans;

// or debug draw by simply extrapolating to the next vert
	for (e = p->edges[0]; e != NULL; e = e->next)
	{
		for (v = e->top, u = e->u; v <= e->bottom; v++, u += e->du)
			R_ClipAndEmitSpan (v, u>>20, u>>20);
//if (v >= 0 && v < r_vars.h && (u>>20) >= 0 && (u>>20) < r_vars.w)
//r_vars.screen[v * r_vars.pitch + (u >> 20)] = 16 * 7;
	}
	for (e = p->edges[1]; e != NULL; e = e->next)
	{
		for (v = e->top, u = e->u; v <= e->bottom; v++, u += e->du)
			R_ClipAndEmitSpan (v, u>>20, u>>20);
//if (v >= 0 && v < r_vars.h && (u>>20) >= 0 && (u>>20) < r_vars.w)
//r_vars.screen[v * r_vars.pitch + (u >> 20)] = 16 * 7;
	}
#endif

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
