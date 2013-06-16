#ifndef __R_SPAN_H__
#define __R_SPAN_H__

/* emitted polygon spans */
struct drawspan_s
{
	short u, v;
	short len;
};


extern void
R_SpanSetup (void);

extern void
R_EmitSpan (short y, short x1, short x2);

extern void
R_BeginSpanFrame (void *buf, int buflen);

extern void
R_DrawGSpans (void);

#endif /* __R_SPAN_H__ */
