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
R_PolyGenEdges (struct mpoly_s *poly, struct viewplane_s *clips[2])
{
	struct drawedge_s *edges;

	if (r_polys == r_polys_end)
		return; //TODO: flush the pipeline and continue on

	edges = R_GenEdges (poly->edges, poly->num_edges, clips);
	if (edges != NULL)
	{
		struct drawpoly_s *p = r_polys++;

		p->edges = edges;
		p->mpoly = poly;
		p->spans = NULL;
		p->num_spans = 0;
	}
}


//TODO: always check for negative-len span before emitting
void
R_ScanPolyEdges (struct drawpoly_s *p)
{
	int u, v;
	struct drawedge_s *e;

	p->spans = r_spans;

// or debug draw by simply extrapolating to the next vert
	for (e = p->edges; e != NULL; e = e->next)
	{
		for (v = e->top, u = e->u; v <= e->bottom; v++, u += e->du)
			R_ClipAndEmitSpan (v, u>>20, u>>20);
//if (v >= 0 && v < r_vars.h && (u>>20) >= 0 && (u>>20) < r_vars.w)
//r_vars.screen[v * r_vars.pitch + (u >> 20)] = 16 * 7;
	}
#if 0
	struct drawedge_s *next = p->edges;
	struct drawedge_s *pop, *pop2;
	int v, next_v;
	int u_l, u_step_l;
	int u_r, u_step_r;

	v = next->top;
	while (1)
	{
		if (v == next->top)
		{
			pop = next;
			next = next->next;

			if (next->top == v)
			{
				/* 2 edges starting on the same scanline */
			}
			else
			{
				/* 1 new edge starting on the scanline */
			}
		}
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
