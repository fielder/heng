#include <stdlib.h>
#include <stdio.h>

#include "bswap.h"
#include "mapfile.h"
#include "map.h"

struct map_s map;


void
Map_LoadVertices (const void *buf, int bufsize)
{
	const struct dvertex_s *dverts = buf;
	int count = bufsize / sizeof(*dverts);
	struct mvertex_s *mverts;
	int i;

	mverts = malloc (sizeof(*mverts) * count);

	for (i = 0; i < count; i++)
	{
		const struct dvertex_s *in = &dverts[i];
		struct mvertex_s *out = &mverts[i];

		out->xyz[0] = LittleFloat (in->xyz[0]);
		out->xyz[1] = LittleFloat (in->xyz[1]);
		out->xyz[2] = LittleFloat (in->xyz[2]);
	}

	if (map.verts != NULL)
	{
		free (map.verts);
		map.verts = NULL;
	}
	map.verts = mverts;
	map.num_verts = count;

	printf ("%d vertices\n", map.num_verts);
}


void
Map_LoadEdges (const void *buf, int bufsize)
{
	const struct dedge_s *dedges = buf;
	int count = bufsize / sizeof(*dedges);
	struct medge_s *medges;
	int i;

	medges = malloc (sizeof(*medges) * count);

	for (i = 0; i < count; i++)
	{
		const struct dedge_s *in = &dedges[i];
		struct medge_s *out = &medges[i];

		out->v[0] = LittleShort (in->verts[0]);
		out->v[1] = LittleShort (in->verts[1]);
		out->cache_index = 0;
	}

	if (map.edges != NULL)
	{
		free (map.edges);
		map.edges = NULL;
	}
	map.edges = medges;
	map.num_edges = count;

	printf ("%d edges\n", map.num_edges);
}


void
Map_LoadPlanes (const void *buf, int bufsize)
{
	const struct dplane_s *dplanes = buf;
	int count = bufsize / sizeof(*dplanes);
	struct mplane_s *mplanes;
	int i;

	mplanes = malloc (sizeof(*mplanes) * count);

	for (i = 0; i < count; i++)
	{
		const struct dplane_s *in = &dplanes[i];
		struct mplane_s *out = &mplanes[i];

		out->normal[0] = LittleFloat (in->normal[0]);
		out->normal[1] = LittleFloat (in->normal[1]);
		out->normal[2] = LittleFloat (in->normal[2]);
		out->dist = LittleFloat (in->dist);

		if (out->normal[0] == 1.0 || out->normal[0] == -1.0)
			out->type = PLANE_X;
		else if (out->normal[1] == 1.0 || out->normal[1] == -1.0)
			out->type = PLANE_Y;
		else if (out->normal[2] == 1.0 || out->normal[2] == -1.0)
			out->type = PLANE_Z;
		else
			out->type = PLANE_OTHER;

		out->signbits = ((out->normal[0] < 0.0) << 0) |
				((out->normal[1] < 0.0) << 1) |
				((out->normal[2] < 0.0) << 2);
	}

	if (map.planes != NULL)
	{
		free (map.planes);
		map.planes = NULL;
	}
	map.planes = mplanes;
	map.num_planes = count;

	printf ("%d planes\n", map.num_planes);
}


void
Map_LoadPolyEdges (const void *buf, int bufsize)
{
	const unsigned short *dpolyedges = buf;
	int count = bufsize / sizeof(*dpolyedges);
	unsigned short *mpolyedges;
	int i;

	mpolyedges = malloc (sizeof(*mpolyedges) * count);

	for (i = 0; i < count; i++)
	{
		const unsigned short *in = &dpolyedges[i];
		unsigned short *out = &mpolyedges[i];

		*out = LittleShort (*in);
	}

	if (map.polyedges != NULL)
	{
		free (map.polyedges);
		map.polyedges = NULL;
	}
	map.polyedges = mpolyedges;
	map.num_polyedges = count;

	printf ("%d polyedges\n", map.num_polyedges);
}


void
Map_LoadPolys (const void *buf, int bufsize)
{
	const struct dpoly_s *dpolys = buf;
	int count = bufsize / sizeof(*dpolys);
	struct mpoly_s *mpolys;
	int i;

	mpolys = malloc (sizeof(*mpolys) * count);

	for (i = 0; i < count; i++)
	{
		const struct dpoly_s *in = &dpolys[i];
		struct mpoly_s *out = &mpolys[i];

		out->plane = &map.planes[LittleShort(in->plane)];
		out->side = LittleShort (in->side);
		out->edges = map.polyedges + LittleShort(in->first_edge);
		out->num_edges = LittleShort (in->num_edges);
	}

	if (map.polys != NULL)
	{
		free (map.polys);
		map.polys = NULL;
	}
	map.polys = mpolys;
	map.num_polys = count;

	printf ("%d polys\n", map.num_polys);
}


void
Map_LoadLeafs (const void *buf, int bufsize)
{
}


void
Map_LoadNodes (const void *buf, int bufsize)
{
}
