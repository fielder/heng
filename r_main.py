import math
import ctypes

import hvars
import io

palettes = []
_cur_pal_idx = -1


def _paletteAtOffset(raw, off):
    pal = []
    for coloridx in xrange(256):
        rgb = raw[off:off + 3]
        off += 3
        pal.append((ord(rgb[0]), ord(rgb[1]), ord(rgb[2])))
    return pal


def init():
    hvars.c_api = ctypes.cdll.LoadLibrary(hvars.RENDER_SO)
    print "Loaded %s" % hvars.RENDER_SO

    hvars.c_api.setup(hvars.screen,
                      hvars.WIDTH,
                      hvars.HEIGHT,
                      hvars.WIDTH,
                      ctypes.c_float(math.radians(hvars.fov)))

    raw = hvars.iwad.readLump("PLAYPAL")
    for off in xrange(0, len(raw), 768):
        palettes.append(_paletteAtOffset(raw, off))
    print "Read %d palettes" % len(palettes)

    setPalette(0)


def refresh():
    # 2D drawing
    #TODO: ...
#   hvars.c_api.drawPalette()

    # 3D drawing
    hvars.c_api.drawWorld()


def setPalette(palidx):
    global _cur_pal_idx

    if palidx != _cur_pal_idx:
        _cur_pal_idx = palidx
        io.setPalette(palettes[_cur_pal_idx])
