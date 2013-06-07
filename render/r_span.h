#ifndef __R_SPAN_H__
#define __R_SPAN_H__

/* green span */
struct gspan_s
{
	struct gspan_s *prev, *next;
	short left, right;
};

/* emitted polygon spans */
struct drawspan_s
{
	short u, v;
	short len;
};


extern void
R_SpanSetup (void);

extern void
R_EmitSpan (int y, int x1, int x2);

extern void
R_BeginSpanFrame (void *buf, int buflen);

extern void
R_DrawGSpans (void);

#endif /* __R_SPAN_H__ */
