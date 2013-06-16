#include <stdint.h>

#include "cdefs.h"

#include "r_poly.h"

static struct drawpoly_s *r_polys = NULL;
static struct drawpoly_s *r_polys_end = NULL;


void
R_BeginPolyFrame (void *buf, int buflen)
{
	/* prepare the given poly buffer */
	uintptr_t p = (uintptr_t)buf;

	while ((p % sizeof(struct drawpoly_s)) != 0)
	{
		p++;
		buflen--;
	}

	r_polys = (struct drawpoly_s *)p;
	r_polys_end = r_polys + (buflen / sizeof(struct drawpoly_s));
}
