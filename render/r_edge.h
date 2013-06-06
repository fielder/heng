#ifndef __R_EDGE_H__
#define __R_EDGE_H__

/* clipped and projected emitted edges */
struct drawedge_s
{
	struct drawedge_s *next; /* in v-sorted list of edges for the poly */

	int u, v;
	int du; /* change in u per y pixel */
	/* no need for a dv as it's always 1 pixel */
};

struct drawpoly_s
{
	struct drawedge_s *edges;
	int num_edges;

	//struct mpoly_s *poly;
};


extern void
R_EdgeSetup (void);

extern void
R_BeginEdgeFrame (void *buf, int buflen);

#endif /* __R_EDGE_H__ */
