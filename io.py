import ctypes

import pygame

import hvars

surf = None
row_buffers = None


def init():
    global surf
    global row_buffers

    # Ideally we'd init only what we need, but this is the only way to
    # initialize pygame's time module. There's no pygame.time.init().
    pygame.init()

    w = hvars.WIDTH
    h = hvars.HEIGHT

    surf = pygame.display.set_mode((w, h), 0, 8)

    hvars.screen = ctypes.create_string_buffer("\x00" * (w * h), w * h)
    print "Allocated %dx%d screen" % (w, h)

    if surf.get_pitch() != w:
        row_buffers = []
        for y in xrange(h):
            row_buffers.append(buffer(hvars.screen, y * w, w))
        print "Using row buffers for %d-pitch screen" % surf.get_pitch()


def shutdown():
    pygame.quit()


def swapBuffer():
    if surf.get_pitch() == surf.get_width():

        # For some seriously wacky reason, we can't pass in hvars.screen
        # directly to the write() method... so we make a temp variable
        # instead. Passing in hvars.screen directly will die, saying the
        # "bytes to write exceed buffer size".
        s = hvars.screen

        surf.get_buffer().write(s, 0)
    else:
        prox = surf.get_buffer()
        dest = 0
        for scanline in row_buffers:
            prox.write(scanline, dest)
            dest += surf.get_pitch()

    pygame.display.flip()

    # calc framerate
    hvars.fps_framecount += 1
    now = pygame.time.get_ticks()
    if (now - hvars.fps_last_start) > 250:
        hvars.fps_rate = hvars.fps_framecount / ((now - hvars.fps_last_start) / 1000.0)
        hvars.fps_last_start = now
        hvars.fps_framecount = 0


def setPalette(pal):
    pygame.display.set_palette(pal)
