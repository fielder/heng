#include <string.h>
#include <stdint.h>

#include "cdefs.h"

#include "render.h"
#include "r_defs.h"
#include "r_span.h"
#include "r_edge.h"
#include "r_poly.h"

static void
R_DrawPolySpans (struct drawpoly_s *p);


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
R_PolyGenEdges (struct mpoly_s *poly)
{
	struct drawedge_s *edges;

	if (r_polys == r_polys_end)
		return; //TODO: flush the pipeline and continue on

	edges = R_GenEdges (poly->edges, poly->num_edges);
	if (edges != NULL)
	{
		struct drawpoly_s *p = r_polys++;

		p->edges = edges;
		p->mpoly = poly;
		p->spans = NULL;
		p->num_spans = 0;
	}
}


void
R_ScanPolyEdges (struct drawpoly_s *p)
{
	//TODO: walk the poly edges, creating spans
	//...
// R_EmitSpan (short y, short x1, short x2)
}


void
R_DrawPolys (void)
{
	struct drawpoly_s *p;

	for (p = r_polys_start; p != r_polys; p++)
		R_DrawPolySpans (p);
}


static void
R_DrawPolySpans (struct drawpoly_s *p)
{
	struct drawspan_s *span;
	int i, color;

	if (!p->num_spans)
		return;

	//TODO: texture mapping magic here

	color = ((uintptr_t)p->mpoly >> 2) & 0xff;

	for (i = 0, span = p->spans; i < p->num_spans; i++, span++)
	{
		memset (r_vars.screen + span->v * r_vars.pitch + span->u,
			color,
			span->len);
	}
}
