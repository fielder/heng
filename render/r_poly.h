#ifndef __R_POLY_H__
#define __R_POLY_H__

#include "map.h"
#include "r_defs.h"

extern void
R_BeginPolyFrame (void *buf, int buflen);

extern void
R_PolyGenEdges (struct mpoly_s *poly);

extern void
R_ScanPolyEdges (struct drawpoly_s *p);

extern void
R_DrawPolys (void);


extern struct drawpoly_s *r_polys;

#endif /* __R_POLY_H__ */
