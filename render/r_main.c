#include <stdint.h>


void
drawPalette(uint8_t *buf, int w, int h, int stride)
{
	int x, y;

	for (y = 0; y < 128 && y < h; y++)
	{
		uint8_t *dest = buf + y * stride;
		for (x = 0; x < 128 && x < w; x++)
			*dest++ = ((y << 1) & 0xf0) + (x >> 3);
	}
}
