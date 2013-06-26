#ifndef __RENDER_H__
#define __RENDER_H__

#include <stdint.h>

#include "r_defs.h"


/* ========================================================== */
/* r_main.c */

extern struct r_vars_s r_vars;

extern void
R_SetupBuffer (uint8_t *buf, int w, int h, int pitch);

extern void
R_SetupProjection (float fov_x);

extern void
R_SetCamera (float pos[3], float angles[3]);

extern void
R_SetDebug (int debug);

extern void
R_Refresh (void);


/* ========================================================== */
/* r_misc.c */

extern void
ClearScreen (void);

extern void
DrawPalette (void);

extern void
DrawLine (int x1, int y1, int x2, int y2, int c);

extern void
DrawLine3D (const float p1[3], const float p2[3], int c);

extern void
DrawGrid (int size, int color);


/* ========================================================== */
/* r_bsp.c */

extern void
R_DrawWorld (void);


/* ========================================================== */
/* r_span.c */

extern struct drawspan_s *r_spans;

extern void
R_SpanSetup (void);

extern void
R_ClipAndEmitSpan (short y, short x1, short x2);

extern void
R_BeginSpanFrame (void *buf, int buflen);

extern void
R_RenderGSpans (void);


/* ========================================================== */
/* r_poly.c */

extern struct drawpoly_s *r_polys;

extern void
R_BeginPolyFrame (void *buf, int buflen);

extern void
R_PolyGenEdges (struct mpoly_s *poly, const struct viewplane_s *cplanes);

extern void
R_ScanPolyEdges (struct drawpoly_s *p);

extern void
R_RenderPolys (void);


/* ========================================================== */
/* r_edge.c */

extern void
R_EdgeSetup (void);

extern void
R_BeginEdgeFrame (void *buf, int buflen);

extern int
R_GenEdges (const unsigned short *edgerefs, int num_edges, const struct viewplane_s *cplanes, struct drawedge_s *out[2]);


/* ========================================================== */
/* r_sprite.c */

extern void
DrawSprite (const void *lump, int x, int y);

extern void
DrawPixmap(const void *pixels, int w, int h, int x, int y);

extern void
DrawSpriteToPixmap (const void *lump, void *out);

#endif /* __RENDER_H__ */
