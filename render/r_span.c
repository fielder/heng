#include <string.h>
#include <stdlib.h>
#include <stdint.h>

#include "render.h"
#include "r_defs.h"
#include "r_span.h"

/* green span */
struct gspan_s
{
	struct gspan_s *prev, *next;
	short left, right;
};

struct drawspan_s *r_spans = NULL;
static struct drawspan_s *r_spans_end = NULL;

static struct gspan_s *r_gspans = NULL;
static struct gspan_s *r_gspans_pool = NULL;


void
R_SpanSetup (void)
{
	struct gspan_s *alloced;
	int i, count;

	if (r_gspans != NULL)
	{
		free (r_gspans);
		r_gspans = NULL;
		r_gspans_pool = NULL;
	}

	/* estimate a probable max number of spans per row */
	count = r_vars.h * 24;

	alloced = malloc (sizeof(*alloced) * count);

	/* The first handful are reserved as each row's gspan
	 * list head. ie: one element per screen row just for
	 * linked-list management. */
	r_gspans = alloced;
	for (i = 0; i < r_vars.h; i++)
		r_gspans[i].prev = r_gspans[i].next = &r_gspans[i];

	r_gspans_pool = alloced + i;
	while (i < count)
	{
		alloced[i].next = (i == count - 1) ? NULL : &alloced[i + 1];
		i++;
	}
}


static void
R_PushSpan (short y, short x1, short x2)
{
	if (r_spans != r_spans_end)
	{
		r_spans->u = x1;
		r_spans->v = y;
		r_spans->len = x2 - x1 + 1;
		r_spans++;
	}
}


void
R_EmitSpan (short y, short x1, short x2)
{
	struct gspan_s *head = &r_gspans[y];
	struct gspan_s *gs, *next, *new;

	gs = head->next;
	while (1)
	{
		if (gs == head)
			break;
		else if (gs->right < x1)
			gs = gs->next;
		else if (gs->left > x2)
			break;
		else if (gs->left < x1)
		{
			/* the gspan hangs off the left of the span,
			 * split the gspan */

			if (r_gspans_pool == NULL)
				return;

			new = r_gspans_pool;
			r_gspans_pool = r_gspans_pool->next;
			new->left = x1;
			new->right = gs->right;
			gs->right = x1 - 1;
			new->prev = gs;
			new->next = gs->next;
			new->prev->next = new;
			new->next->prev = new;
			gs = new;
		}
		else if (gs->right <= x2)
		{
			/* the gspan lies entirely within the span,
			 * emit a drawable span */
			R_PushSpan (y, gs->left, gs->right);
			next = gs->next;
			gs->prev->next = gs->next;
			gs->next->prev = gs->prev;
			gs->next = r_gspans_pool;
			r_gspans_pool = gs;
			gs = next;
		}
		else
		{
			/* the gspan hangs off the right of the span,
			 * split the gspan */

			if (r_gspans_pool == NULL)
				return;

			new = r_gspans_pool;
			r_gspans_pool = r_gspans_pool->next;
			new->left = x2 + 1;
			new->right = gs->right;
			gs->right = x2;
			new->prev = gs;
			new->next = gs->next;
			new->prev->next = new;
			new->next->prev = new;
		}
	}
}


void
R_BeginSpanFrame (void *buf, int buflen)
{
	/* prepare the given span buffer */
	uintptr_t p = (uintptr_t)buf;
	int i;

	while ((p % sizeof(struct drawspan_s)) != 0)
	{
		p++;
		buflen--;
	}

	r_spans = (struct drawspan_s *)p;
	r_spans_end = r_spans + (buflen / sizeof(struct drawspan_s));

	/* now gspans */
	struct gspan_s *gs, *head, *next;

	for (i = 0, head = r_gspans; i < r_vars.h; i++, head++)
	{
		/* take any gspan still remaining on the row and toss
		 * back into the pool */
		while ((next = head->next) != head)
		{
			head->next = next->next;
			next->next = r_gspans_pool;
			r_gspans_pool = next;
		}

		/* reset the row with 1 fresh gspan */

		gs = r_gspans_pool;
		r_gspans_pool = gs->next;

		gs->left = 0;
		gs->right = r_vars.w - 1;
		gs->prev = gs->next = head;
		head->prev = head->next = gs;
	}
}


/*
 * Draw any remaining gspan on the screen. In normal operation, the
 * screen should be filled by the rendered world so there should never
 * be any gspans visible.
 */
void
R_RenderGSpans (void)
{
	const struct gspan_s *gs;
	int i;

	for (i = 0; i < r_vars.h; i++)
	{
		for (gs = r_gspans[i].next; gs != &r_gspans[i]; gs = gs->next)
		{
			memset (r_vars.screen + i * r_vars.pitch + gs->left,
				251,
				gs->right - gs->left + 1);
		}
	}
}
