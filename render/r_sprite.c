#include "r_defs.h"


static void
drawColumn (const uint8_t *posts, int x, int y)
{
	const struct r_post_s *p = (const struct r_post_s *)posts;
	const uint8_t *pixels;
	uint8_t *base_dest, *dest;
	int c;

	base_dest = r_buf.screen + y * r_buf.pitch + x;

	while (p->topdelta != 0xff)
	{
		pixels = (const uint8_t *)p + 3;
		c = p->length;
		dest = base_dest + p->topdelta * r_buf.pitch;

		while (c--)
		{
			*dest = *pixels++;
			dest += r_buf.pitch;
		}

		p = (const struct r_post_s *)((uint8_t *)p + p->length + 4);
	}
}


//TODO: use offsets properly
void
drawSprite (const uint8_t *lump, int x, int y)
{
	int i;
	const struct r_patch_s *p = (const struct r_patch_s *)lump;

	for (i = 0; i < p->width; i++)
		drawColumn (lump + p->columnofs[i], x + i, y);
}
