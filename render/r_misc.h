#ifndef __R_MISC_H__
#define __R_MISC_H__

extern void
ClearScreen (void);

extern void
DrawPalette (void);

extern void
DrawLine (int x1, int y1, int x2, int y2, int c);

struct viewpos_s
{
	float pos[3];
	float angles[3];
	const char *name;

	struct viewpos_s *next;
};

extern void
PrintViewPos (void);

extern void
RestoreViewPos (const char *name);

extern void
PushViewPos (const char *name);

#endif /* __R_MISC_H__ */
