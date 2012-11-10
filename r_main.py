import ctypes

import hvars
import io

RENDER_SO = "./render.so"

palettes = []
cur_pal_idx = -1
c_api = None


def init():
    global palettes
    global c_api

    c_api = ctypes.cdll.LoadLibrary(RENDER_SO)
    print "loaded %s" % RENDER_SO

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
    c_api.drawPalette(hvars.screen, hvars.WIDTH, hvars.HEIGHT, hvars.WIDTH)

    io.swapBuffer()


def setPalette(palidx):
    global cur_pal_idx

    if palidx != cur_pal_idx:
        cur_pal_idx = palidx
        io.setPalette(palettes[cur_pal_idx])
