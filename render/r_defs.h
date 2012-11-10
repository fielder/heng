#ifndef __R_DEFS_H__
#define __R_DEFS_H__

#include <stdint.h>

struct r_buf_s
{
	int w, h, pitch;
	uint8_t *screen;
};

struct r_view_s
{
	float xxx;
};

extern struct r_buf_s r_buf;
extern struct r_view_s r_view;

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
	uint8_t topdelta; /* 0xff is last post in a column */
	uint8_t length; /* <length> data bytes follow */
};

#endif /* __R_DEFS_H__ */
