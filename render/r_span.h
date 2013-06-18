#ifndef __R_SPAN_H__
#define __R_SPAN_H__

#include "r_defs.h"

extern struct drawspan_s *r_spans;


extern void
R_SpanSetup (void);

extern void
R_EmitSpan (short y, short x1, short x2);

extern void
R_BeginSpanFrame (void *buf, int buflen);

extern void
R_RenderGSpans (void);

#endif /* __R_SPAN_H__ */
