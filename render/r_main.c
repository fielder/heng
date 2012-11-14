#include <stdint.h>
#include <math.h>
#include <string.h>

#include "r_defs.h"
#include "vec.h"

static void
initCamera (float);

static void
cameraChanged (void);

struct r_defs_s r_defs;


void
setup (uint8_t *buf, int w, int h, int pitch, float fov_x)
{
	r_defs.screen = buf;
	r_defs.w = w;
	r_defs.h = h;
	r_defs.pitch = pitch;

	initCamera (fov_x);
}


void
drawPalette (void)
{
	int x, y;

	for (y = 0; y < 128 && y < r_defs.h; y++)
	{
		uint8_t *dest = r_defs.screen + y * r_defs.pitch;
		for (x = 0; x < 128 && x < r_defs.w; x++)
			*dest++ = ((y << 1) & 0xf0) + (x >> 3);
	}
}


static void
initCamera (float fov_x)
{
	r_defs.center_x = r_defs.w / 2.0 - 0.5;
	r_defs.center_y = r_defs.h / 2.0 - 0.5;

	r_defs.fov_x = fov_x;
	r_defs.dist = (r_defs.w / 2.0) / tan(r_defs.fov_x / 2.0);
	r_defs.fov_y = 2.0 * atan((r_defs.h / 2.0) / r_defs.dist);

	Vec_Clear (r_defs.pos);
	Vec_Clear (r_defs.angles);

	r_defs.angles[1] = M_PI; /* start off looking to +z axis */

	cameraChanged ();
}


static void
cameraChanged (void)
{
	float v[3];

	/* make transformation matrix */
	Vec_Copy (r_defs.angles, v);
	Vec_Scale (v, -1.0);
	Vec_AnglesMatrix (v, r_defs.xform, ROT_MATRIX_ORDER_XYZ);

	/* We're looking down the -z axis, and our projection calculation
	 * assumes greater z is further away. So negate z values so
	 * positive z objects are behind the camera. */
	Vec_Scale (r_defs.xform[2], -1.0);

	/* get view vectors */
	Vec_Copy (r_defs.xform[0], r_defs.right);
	Vec_Copy (r_defs.xform[1], r_defs.up);
	Vec_Copy (r_defs.xform[2], r_defs.forward);

	//TODO: setup view planes
}


void
cameraRotatePixels (float dx, float dy)
{
	/* using right-handed coordinate system, so positive yaw goes
	 * left across the screen and positive roll goes up */
	r_defs.angles[YAW] += r_defs.fov_x * (-dx / r_defs.w);
	r_defs.angles[PITCH] += r_defs.fov_y * (-dy / r_defs.h);

	/* restrict camera angles */
	if (r_defs.angles[PITCH] > M_PI / 2.0)
		r_defs.angles[PITCH] = M_PI / 2.0;
	if (r_defs.angles[PITCH] < -M_PI / 2.0)
		r_defs.angles[PITCH] = -M_PI / 2.0;

	while (r_defs.angles[YAW] >= M_PI * 2.0)
		r_defs.angles[YAW] -= M_PI * 2.0;
	while (r_defs.angles[YAW] < 0.0)
		r_defs.angles[YAW] += M_PI * 2.0;

	cameraChanged ();
}


void
cameraThrust (float right, float up, float forward)
{
	float v[3];

	Vec_Copy (r_defs.right, v);
	Vec_Scale (v, right);
	Vec_Add (r_defs.pos, v, r_defs.pos);

	Vec_Copy (r_defs.up, v);
	Vec_Scale (v, up);
	Vec_Add (r_defs.pos, v, r_defs.pos);

	Vec_Copy (r_defs.forward, v);
	Vec_Scale (v, forward);
	Vec_Add (r_defs.pos, v, r_defs.pos);

	cameraChanged ();
}


static void
transformVec (const float v[3], float out[3])
{
	int i;

	for (i = 0; i < 3; i++)
		out[i] = Vec_Dot (r_defs.xform[i], v);
}


void
clearScreen (void)
{
	int y;

	if (((uintptr_t)r_defs.screen & 0x3) == 0 && (r_defs.w % 4) == 0)
	{
		for (y = 0; y < r_defs.h; y++)
		{
			int w2 = r_defs.w >> 2;
			uint32_t *dest = (uint32_t *)(r_defs.screen + y * r_defs.pitch);
			while (w2--)
				*dest++ = 0;
		}
	}
	else
	{
		for (y = 0; y < r_defs.h; y++)
			memset (r_defs.screen + y * r_defs.pitch, 0, r_defs.w);
	}
}


void
drawWorld (void)
{
	int i;
	float p[8][3];
	float local[3], n[3];
	float *v, zi;
	int uu, vv;

	clearScreen ();

	p[0][0] = 0.0;
	p[0][1] = 0.0;
	p[0][2] = 128.0;
	p[1][0] = 32.0;
	p[1][1] = 0.0;
	p[1][2] = 128.0;
	p[2][0] = 32.0;
	p[2][1] = 0.0;
	p[2][2] = 128.0 + 32;
	p[3][0] = 0.0;
	p[3][1] = 0.0;
	p[3][2] = 128.0 + 32;

	p[4][0] = 0.0;
	p[4][1] = 64.0;
	p[4][2] = 128.0;
	p[5][0] = 32.0;
	p[5][1] = 64.0;
	p[5][2] = 128.0;
	p[6][0] = 32.0;
	p[6][1] = 64.0;
	p[6][2] = 128.0 + 32;
	p[7][0] = 0.0;
	p[7][1] = 64.0;
	p[7][2] = 128.0 + 32;

	for (i = 0; i < 8; i++)
	{
		v = p[i];
		Vec_Subtract (v, r_defs.pos, local);
		transformVec (local, n);
		if (n[2] > 0.0)
		{
			zi = 1.0 / n[2];
			uu = (int)(r_defs.center_x + r_defs.dist * zi * n[0]);
			vv = (int)(r_defs.center_y - r_defs.dist * zi * n[1]);
			if (uu >= 0 && uu < r_defs.w && vv >= 0 && vv < r_defs.h)
			{
				r_defs.screen[vv * r_defs.pitch + uu] = 4;
			}
		}
	}
}
