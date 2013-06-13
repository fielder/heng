import math
import ctypes

import misc
import hvars
import io
import r_pic
import console
from utils import pcx

palettes = []
_cur_pal_idx = -1


def _paletteAtOffset(raw, off):
    return [(ord(rgb[0]), ord(rgb[1]), ord(rgb[2])) for rgb in misc.chopSequence(raw, 3)]


def init():
    hvars.c_api = ctypes.cdll.LoadLibrary(hvars.RENDER_SO)
    print "Loaded %s" % hvars.RENDER_SO

    hvars.c_api.Setup(hvars.screen,
                      hvars.WIDTH,
                      hvars.HEIGHT,
                      hvars.WIDTH,
                      ctypes.c_float(math.radians(hvars.fov)))

    raw = hvars.iwad.readLump("PLAYPAL")
    for off in xrange(0, len(raw), 768):
        palettes.append(_paletteAtOffset(raw, off))
    print "Read %d palettes" % len(palettes)

    r_pic.init()

    setPalette(0)

p_tex = None


def refresh():
    global p_tex
    global p_w
    global p_h

    if not p_tex:
        name = "TOMW2_1"
        p_tex = r_pic.getPixmap(name)
#       hvars.c_api.SetTexture(p_tex.pixels, p_tex.w, p_tex.h)
        print name, p_tex.w, p_tex.h

    hvars.c_api.ClearScreen()

    # 2D drawing
    #TODO: ...
#   hvars.c_api.DrawPalette()
#   hvars.c_api.DrawLine(50, 50, 100, 200, 4)

    # 3D drawing
    hvars.c_api.DrawWorld()

    if console.up:
        console.draw(hvars.HEIGHT - (hvars.HEIGHT / 4))


def setPalette(palidx):
    global _cur_pal_idx

    if palidx != _cur_pal_idx:
        _cur_pal_idx = palidx
        io.setPalette(palettes[_cur_pal_idx])
