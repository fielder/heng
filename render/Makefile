CC = gcc
CFLAGS = -Wall -O2 -fPIC -march=native
LDFLAGS = -lm
OBJDIR = .

TARGET = $(OBJDIR)/render.so

OBJS =	$(OBJDIR)/bswap.o \
	$(OBJDIR)/vec.o \
	$(OBJDIR)/r_main.o \
	$(OBJDIR)/r_misc.o \
 	$(OBJDIR)/r_span.o \
 	$(OBJDIR)/map.o

#	$(OBJDIR)/r_edge.o
#	$(OBJDIR)/r_sprite.o \

all: $(TARGET)

clean:
	rm -f $(OBJDIR)/*.o
	rm -f $(TARGET)

$(TARGET): $(OBJS)
	$(CC) -shared $(OBJS) -o $(TARGET) $(LDFLAGS)

########################################################################

$(OBJDIR)/bswap.o: bswap.c
	$(CC) -c $(CFLAGS) $? -o $@
$(OBJDIR)/vec.o: vec.c
	$(CC) -c $(CFLAGS) $? -o $@

$(OBJDIR)/r_main.o: r_main.c
	$(CC) -c $(CFLAGS) $? -o $@
$(OBJDIR)/r_misc.o: r_misc.c
	$(CC) -c $(CFLAGS) $? -o $@
$(OBJDIR)/r_span.o: r_span.c
	$(CC) -c $(CFLAGS) $? -o $@
$(OBJDIR)/map.o: map.c
	$(CC) -c $(CFLAGS) $? -o $@

$(OBJDIR)/r_edge.o: r_edge.c
	$(CC) -c $(CFLAGS) $? -o $@
$(OBJDIR)/r_sprite.o: r_sprite.c
	$(CC) -c $(CFLAGS) $? -o $@
