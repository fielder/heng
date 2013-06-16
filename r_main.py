import math
import ctypes

import hvars
import hio
#import r_pic
#import console

palettes = []
_cur_pal_idx = -1


def init():
    hvars.c_api = ctypes.cdll.LoadLibrary(hvars.RENDER_SO)
    print "Loaded %s" % hvars.RENDER_SO

    hvars.c_api.R_SetupBuffer(hvars.screen, hvars.WIDTH, hvars.HEIGHT, hvars.WIDTH)

    raw = hvars.iwad.readLump("PLAYPAL")
    for off in xrange(0, len(raw), 768):
        palettes.append(_paletteAtOffset(raw, off))
    print "Read %d palettes" % len(palettes)

#   r_pic.init()

    setPalette(0)


def refresh():
    hvars.c_api.ClearScreen()

    # 2D drawing
    #TODO: ...

    # 3D drawing
    hvars.c_api.R_Refresh()

#   if console.up:
#       console.draw(hvars.HEIGHT - (hvars.HEIGHT / 4))


def setPalette(palidx):
    global _cur_pal_idx

    if palidx != _cur_pal_idx:
        _cur_pal_idx = palidx
        hio.setPalette(palettes[_cur_pal_idx])

def _chopSequence(sequence, chunksize):
    idx = 0
    while idx < len(sequence):
        yield sequence[idx:idx + chunksize]
        idx += chunksize

def _paletteAtOffset(raw, off):
    return [(ord(rgb[0]), ord(rgb[1]), ord(rgb[2])) for rgb in _chopSequence(raw, 3)]
