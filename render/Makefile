CC = gcc
CFLAGS = -Wall -O2 -fPIC
OBJDIR = .

TARGET = $(OBJDIR)/render.so

OBJS =	$(OBJDIR)/bswap.o \
	$(OBJDIR)/vec.o \
	$(OBJDIR)/r_main.o

all: $(TARGET)

clean:
	rm -f $(OBJDIR)/*.o
	rm -f $(TARGET)

$(TARGET): $(OBJS)
	$(CC) -shared $(OBJS) -o $(TARGET)

########################################################################

$(OBJDIR)/bswap.o: bswap.c
	$(CC) -c $(CFLAGS) $? -o $@
$(OBJDIR)/vec.o: vec.c
	$(CC) -c $(CFLAGS) $? -o $@
$(OBJDIR)/r_main.o: r_main.c
	$(CC) -c $(CFLAGS) $? -o $@
