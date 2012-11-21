#ifndef __R_DEFS_H__
#define __R_DEFS_H__

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

#endif /* __R_DEFS_H__ */
