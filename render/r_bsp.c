#include "cdefs.h"
#include "vec.h"

#include "map.h"
#include "render.h"


void
BSP_DrawWorld (void)
{
	char spanbuf[0x8000];
	char edgebuf[0x8000];
	char polybuf[0x8000];

	struct viewplane_s *cplanes;

	S_BeginSpanFrame (spanbuf, sizeof(spanbuf));
	E_BeginEdgeFrame (edgebuf, sizeof(edgebuf));
	P_BeginPolyFrame (polybuf, sizeof(polybuf));

	cplanes = &r_vars.vplanes[0];
	r_vars.vplanes[0].next = &r_vars.vplanes[1];
	r_vars.vplanes[1].next = &r_vars.vplanes[2];
	r_vars.vplanes[2].next = &r_vars.vplanes[3];
	r_vars.vplanes[3].next = NULL;

	DrawGrid (1024, 16 * 7 - 2);

	{
		struct drawpoly_s *cluster_start;
		struct mpoly_s *p;
		int i;
		bool on_back;

		cluster_start = r_polys;

		for (i = 0, p = map.polys; i < map.num_polys; i++, p++)
		{
			on_back = Vec_Dot(p->plane->normal, r_vars.pos) - p->plane->dist < BACKFACE_DIST;
			if (p->side != on_back)
				continue;

			P_PolyGenEdges (p, cplanes);
		}

		while (cluster_start != r_polys)
			P_ScanPolyEdges (cluster_start++);
	}

	P_RenderPolys ();

	if (0)
		S_RenderGSpans();

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
