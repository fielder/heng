#ifndef __R_EDGE_H__
#define __R_EDGE_H__

#include "r_defs.h"

extern void
R_EdgeSetup (void);

extern void
R_BeginEdgeFrame (void *buf, int buflen);

extern int
R_GenEdges (const unsigned short *edgerefs, int num_edges, const struct viewplane_s *cplanes, struct drawedge_s *out[2]);

#endif /* __R_EDGE_H__ */
