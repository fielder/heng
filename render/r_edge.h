#ifndef __R_EDGE_H__
#define __R_EDGE_H__

/* clipped and projected emitted edges */
struct drawedge_s
{
	struct drawedge_s *next; /* in v-sorted list of edges for the poly */

	int top, bottom;
	int u, du; /* 12.20 */
	/* no need for a dv as it's always 1 pixel */
};


extern void
R_EdgeSetup (void);

extern void
R_BeginEdgeFrame (void *buf, int buflen);

#endif /* __R_EDGE_H__ */
