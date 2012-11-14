import types
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
    pygame.event.set_grab(False)
    pygame.mouse.set_visible(True)
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
    now = milliSeconds()
    if (now - hvars.fps_last_start) > 250:
        hvars.fps_rate = hvars.fps_framecount / ((now - hvars.fps_last_start) / 1000.0)
        hvars.fps_last_start = now
        hvars.fps_framecount = 0


def setPalette(pal):
    pygame.display.set_palette(pal)


def milliSeconds():
    return pygame.time.get_ticks()

########################################################################

_key_names = {} # name -> int
_binds = {} # int/str -> func

# number of mouse motions to ignore right after grabbing the mouse; used
# to avoid a huge initial mouse delta when grabbing
_ignore_mousemove = 1

for item_name in dir(pygame):
    if item_name.startswith("K_"):
        _key_names[item_name[2:].lower()] = getattr(pygame, item_name)
del(_key_names["last"]) # not a real key


def toggleGrab():
    global _ignore_mousemove

    grabbed = not pygame.event.get_grab()
    pygame.event.set_grab(grabbed)
    pygame.mouse.set_visible(not grabbed)

    _ignore_mousemove = 1


def bind(obj, func):
    """
    Caller can give an SDL key integer, a key name string, a button in
    the format "buttonX", or "mousemove".
    """

    if type(obj) == types.StringType:
        if obj.startswith("button"):
            pass
        elif obj == "mousemove":
            pass
        else:
            if obj not in _key_names:
                raise Exception("unknown key \"%s\"" % obj)
            obj = _key_names[obj]
    elif type(obj) != types.IntType:
        raise Exception("invalid bindable \"%s\"" % str(obj))

    _binds[obj] = func


def runInput():
    global _ignore_mousemove

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            hvars.do_quit = 1
        elif ev.type == pygame.KEYDOWN:
            if ev.key in _binds and _binds[ev.key]:
                _binds[ev.key]()
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            b = "button%d" % ev.button
            if b in _binds and _binds[b]:
                _binds[b]()
        elif ev.type == pygame.MOUSEMOTION:
            delta = pygame.mouse.get_rel()
            if pygame.event.get_grab():
                if _ignore_mousemove == 0:
                    if "mousemove" in _binds and _binds["mousemove"]:
                        _binds["mousemove"](delta)
                else:
                    _ignore_mousemove -= 1
        else:
            pass
