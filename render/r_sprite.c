#include <stdint.h>
#include <string.h>

#include "render.h"

struct r_patch_s
{
	short width;
	short height;
	short leftoffset; /* pixels to the left of origin */
	short topoffset; /* pixels below the origin */
	int columnofs[0]; /* variable sized */
};

struct r_post_s
{
	unsigned char topdelta; /* 0xff is last post in a column */
	unsigned char length; /* <length> data bytes follow */
};


//FIXME: clip y
static void
DrawColumn (const uint8_t *posts, int x, int y)
{
	const struct r_post_s *p = (const struct r_post_s *)posts;
	const uint8_t *pixels;
	uint8_t *base_dest, *dest;
	int c;

	base_dest = r_vars.screen + y * r_vars.pitch + x;

	while (p->topdelta != 0xff)
	{
		pixels = (const uint8_t *)p + 3;
		c = p->length;
		dest = base_dest + p->topdelta * r_vars.pitch;

		while (c--)
		{
			*dest = *pixels++;
			dest += r_vars.pitch;
		}

		p = (const struct r_post_s *)((uint8_t *)p + p->length + 4);
	}
}


//TODO: use offsets properly
void
DrawSprite (const void *lump, int x, int y)
{
	const struct r_patch_s *p = (const struct r_patch_s *)lump;
	int colidx = 0;
	int w = p->width;

	if (y < 0 || y + p->height > r_vars.h)
		return;

	if (x < 0)
	{
		colidx += -x;
		w -= -x;
		x = 0;
	}
	if (x + w > r_vars.w)
		w = r_vars.w - x;

	if (w <= 0)
		return;

	while (w--)
		DrawColumn (lump + p->columnofs[colidx++], x++, y);
}


void
DrawPixmap(const void *pixels, int w, int h, int x, int y)
{
	const uint8_t *src = pixels;
	uint8_t *dest;
	int draw_w = w;

	/* clip left */
	if (x < 0)
	{
		src += -x;
		draw_w -= -x;
		x = 0;
	}

	/* clip right */
	if (x + draw_w > r_vars.w)
		draw_w = r_vars.w - x;

	if (draw_w <= 0)
		return;

	/* clip top */
	if (y < 0)
	{
		src += -y * w;
		h -= -y;
		y = 0;
	}

	/* clip bottom */
	if (y + h > r_vars.h)
		h = r_vars.h - y;

	if (h <= 0)
		return;

	dest = r_vars.screen + y * r_vars.pitch + x;
	while (h--)
	{
		memcpy (dest, src, draw_w);
		src += w;
		dest += r_vars.pitch;
	}
}


static void
WriteSpriteColumn (const uint8_t *posts, int x, uint8_t *pixmap, int w, int h)
{
	const struct r_post_s *p = (const struct r_post_s *)posts;
	const uint8_t *pixels;
	uint8_t *dest_top, *dest;
	int c;

	dest_top = pixmap + x;

	while (p->topdelta != 0xff)
	{
		pixels = (const uint8_t *)p + 3;
		c = p->length;
		dest = dest_top + p->topdelta * w;

		while (c--)
		{
			*dest = *pixels++;
			dest += w;
		}

		p = (const struct r_post_s *)((uint8_t *)p + p->length + 4);
	}
}


void
DrawSpriteToPixmap (const void *lump, void *out)
{
	const struct r_patch_s *p = (const struct r_patch_s *)lump;
	int i;

	for (i = 0; i < p->width; i++)
		WriteSpriteColumn (lump + p->columnofs[i], i, out, p->width, p->height);
}
