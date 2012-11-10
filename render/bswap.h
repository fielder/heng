#ifndef __BSWAP_H__
#define __BSWAP_H__

extern int
SwapInit (void); /* returns 0 on little, 1 on big-endianed hosts */

extern short
SwapShort (short s);

extern int
SwapInt (int i);

extern float
SwapFloat (float f);

extern short
NoSwapShort (short s);

extern int
NoSwapInt (int i);

extern float
NoSwapFloat (float f);

extern short (*LittleShort) (short s);
extern int (*LittleInt) (int i);
extern float (*LittleFloat) (float f);
extern short (*BigShort) (short s);
extern int (*BigInt) (int i);
extern float (*BigFloat) (float f);

#endif /* __BSWAP_H__ */
