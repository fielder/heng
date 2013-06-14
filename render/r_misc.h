#ifndef __R_MISC_H__
#define __R_MISC_H__

extern void
ClearScreen (void);

extern void
DrawPalette (void);

extern void
DrawLine (int x1, int y1, int x2, int y2, int c);

extern void
DrawGrid (int size, int color);

#endif /* __R_MISC_H__ */
