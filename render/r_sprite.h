#ifndef __R_SPRITE_H__
#define __R_SPRITE_H__

extern void
DrawSprite (const void *lump, int x, int y);

extern void
DrawPixmap(const void *pixels, int w, int h, int x, int y);

extern void
DrawSpriteToPixmap (const void *lump, void *out);

#endif /* __R_SPRITE_H__ */
