#ifndef __R_POLY_H__
#define __R_POLY_H__

#include "map.h"
#include "render.h"
#include "r_defs.h"

extern struct drawpoly_s *r_polys;


extern void
R_BeginPolyFrame (void *buf, int buflen);

extern void
R_PolyGenEdges (struct mpoly_s *poly, struct viewplane_s *cplanes);

extern void
R_ScanPolyEdges (struct drawpoly_s *p);

extern void
R_RenderPolys (void);

#endif /* __R_POLY_H__ */
