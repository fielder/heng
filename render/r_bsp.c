#include "cdefs.h"
#include "vec.h"

#include "map.h"
#include "render.h"
#include "r_misc.h"
#include "r_span.h"
#include "r_edge.h"
#include "r_poly.h"
#include "r_bsp.h"


void
R_DrawWorld (void)
{
	char spanbuf[0x8000];
	char edgebuf[0x8000];
	char polybuf[0x8000];

	struct viewplane_s *clips[2];

	R_BeginSpanFrame (spanbuf, sizeof(spanbuf));
	R_BeginEdgeFrame (edgebuf, sizeof(edgebuf));
	R_BeginPolyFrame (polybuf, sizeof(polybuf));

	r_vars.vplanes[VPLANE_TOP].next = &r_vars.vplanes[VPLANE_BOTTOM];
	r_vars.vplanes[VPLANE_BOTTOM].next = NULL;
	clips[CPLANES_TOP_BOTTOM] = &r_vars.vplanes[VPLANE_TOP];

	r_vars.vplanes[VPLANE_LEFT].next = &r_vars.vplanes[VPLANE_RIGHT];
	r_vars.vplanes[VPLANE_RIGHT].next = NULL;
	clips[CPLANES_LEFT_RIGHT] = &r_vars.vplanes[VPLANE_LEFT];

	DrawGrid (1024, 16 * 7 - 2);

	{
		struct drawpoly_s *cluster_start;
		struct mpoly_s *p;
		int i;
		bool on_back;

		cluster_start = r_polys;

map.num_polys = 1;//DEBUG
		for (i = 0, p = map.polys; i < map.num_polys; i++, p++)
		{
			on_back = Vec_Dot(p->plane->normal, r_vars.pos) - p->plane->dist < BACKFACE_DIST;
			if (p->side != on_back)
				continue;

			R_PolyGenEdges (p, clips);
		}

		while (cluster_start != r_polys)
			R_ScanPolyEdges (cluster_start++);
	}

	R_RenderPolys ();

	if (0)
		R_RenderGSpans();

	// - edge drawing for all polys in the leaf and all polys on
	//   the parent node
	// - emit spans for each emitted poly

	// - then iterate over node portals
	// - one at a time, run edge drawing and span emitting
	// - if a single span is visible, stop drawing portals
	//   and traverse the back side of the node

#if 0
if (1)
{
	int i;
	for (i = 0; i < map.num_polys; i++)
	{
		const struct mpoly_s *p = &map.polys[i];
		int j, on_back;

		on_back = Vec_Dot(r_vars.pos, p->plane->normal) - p->plane->dist < 0.01;
		if (p->side != on_back)
			continue;

		for (j = 0; j < p->num_edges; j++)
		{
			int edgenum = p->edges[j] & 0x7fff;
			const struct medge_s *edge = &map.edges[edgenum];
		DrawLine3D (	map.verts[edge->v[0]].xyz,
				map.verts[edge->v[1]].xyz,
				16 * 7);
		}
	}
}
if (0)
{
	int i;
	for (i = 0; i < map.num_edges; i++)
	{
		DrawLine3D (	map.verts[map.edges[i].v[0]].xyz,
				map.verts[map.edges[i].v[1]].xyz,
				16 * 7);
	}
}
#endif
}
