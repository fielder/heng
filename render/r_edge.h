#ifndef __R_EDGE_H__
#define __R_EDGE_H__

#include "r_defs.h"

extern void
R_EdgeSetup (void);

extern void
R_BeginEdgeFrame (void *buf, int buflen);

extern struct drawedge_s *
R_GenEdges (const unsigned short *edgerefs, int num_edges);

#endif /* __R_EDGE_H__ */
