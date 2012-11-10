import ctypes

import hvars
import io

RENDER_SO = "./render.so"

palettes = []
cur_pal_idx = -1
c_api = None

PLAYA1 = None


def init():
    global palettes
    global c_api

    c_api = ctypes.cdll.LoadLibrary(RENDER_SO)
    print "loaded %s" % RENDER_SO

    c_api.setup(hvars.screen, hvars.WIDTH, hvars.HEIGHT, hvars.WIDTH)

    raw = hvars.iwad.readLump("PLAYPAL")
    idx = 0
    while idx < len(raw):
        pal = []
        for coloridx in xrange(256):
            rgb = raw[idx:idx + 3]
            idx += 3
            pal.append((ord(rgb[0]), ord(rgb[1]), ord(rgb[2])))
        palettes.append(pal)
    print "read %d palettes" % len(palettes)

    setPalette(0)


def refresh():
    global PLAYA1

    if not PLAYA1:
        PLAYA1 = hvars.iwad.readLump("PLAYA1")

    c_api.drawPalette()
    c_api.drawSprite(PLAYA1, 200, 50)

    io.swapBuffer()


def setPalette(palidx):
    global cur_pal_idx

    if palidx != cur_pal_idx:
        cur_pal_idx = palidx
        io.setPalette(palettes[cur_pal_idx])
