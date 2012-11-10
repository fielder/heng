#include "bswap.h"

short (*LittleShort) (short s);
int (*LittleInt) (int i);
float (*LittleFloat) (float f);
short (*BigShort) (short s);
int (*BigInt) (int i);
float (*BigFloat) (float f);


int
SwapInit (void)
{
	union
	{
		int i;
		short s;
		char c;
	} u;
	int endianess;

	u.i = 0;
	u.c = 1;
	if (u.s == 1)
	{
		LittleShort	= NoSwapShort;
		LittleInt	= NoSwapInt;
		LittleFloat	= NoSwapFloat;
		BigShort	= SwapShort;
		BigInt		= SwapInt;
		BigFloat	= SwapFloat;
		endianess = 0;
	}
	else
	{
		LittleShort	= SwapShort;
		LittleInt	= SwapInt;
		LittleFloat	= SwapFloat;
		BigShort	= NoSwapShort;
		BigInt		= NoSwapInt;
		BigFloat	= NoSwapFloat;
		endianess = 1;
	}

	return endianess;
}


short
SwapShort (short s)
{
	int b1, b2;
	b1 = s & 0xff;
	b2 = (s >> 8) & 0xff;
	return (b1 << 8) | b2;
}


int
SwapInt (int i)
{
	int b1, b2, b3, b4;
	b1 = i & 0xff;
	b2 = (i >> 8) & 0xff;
	b3 = (i >> 16) & 0xff;
	b4 = (i >> 24) & 0xff;
	return (b1 << 24) | (b2 << 16) | (b3 << 8) | b4;
}


float
SwapFloat (float f)
{
	union {
		float f;
		char b[4];
	} x, y;
	x.f = f;
	y.b[0] = x.b[3];
	y.b[1] = x.b[2];
	y.b[2] = x.b[1];
	y.b[3] = x.b[0];
	return y.f;
}


short
NoSwapShort (short s)
{
	return s;
}


int
NoSwapInt (int i)
{
	return i;
}


float
NoSwapFloat (float f)
{
	return f;
}


#if 0

#include <stdio.h>

int
main (int argc, const char *argv[])
{
	int i = SwapInit ();
	printf ("%s endian host\n", i ? "big" : "little");
	return 0;
}

#endif
