#ifndef __R_POLY_H__
#define __R_POLY_H__

#include "map.h"
#include "r_span.h"
#include "r_edge.h"

struct drawpoly_s
{
	struct drawedge_s *edges;

	struct drawspan_s *spans;
	int num_spans;

	struct mpoly_s *mpoly;
};


extern void
R_BeginPolyFrame (void *buf, int buflen);

#endif /* __R_POLY_H__ */
