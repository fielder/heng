import ctypes

import hvars
import cdefs
import io
import r_camera

palettes = []
cur_pal_idx = -1
c_api = None


def _paletteAtOffset(raw, off):
    pal = []
    for coloridx in xrange(256):
        rgb = raw[off:off + 3]
        off += 3
        pal.append((ord(rgb[0]), ord(rgb[1]), ord(rgb[2])))
    return pal


def init():
    global palettes
    global c_api

    c_api = ctypes.cdll.LoadLibrary(hvars.RENDER_SO)
    print "Loaded %s" % hvars.RENDER_SO

    c_api.setup(hvars.screen, hvars.WIDTH, hvars.HEIGHT, hvars.WIDTH)

    raw = hvars.iwad.readLump("PLAYPAL")
    for off in xrange(0, len(raw), 768):
        palettes.append(_paletteAtOffset(raw, off))
    print "Read %d palettes" % len(palettes)

    setPalette(0)

    r_camera.init()


def refresh():
    # 2D drawing
    #TODO: ...

    # 3D drawing
    c_api.setCamera(ctypes.c_float(hvars.camera.fov_x),
                    cdefs.Vec3(*hvars.camera.pos),
                    cdefs.Vec3(*hvars.camera.angles))
#   c_api.drawWorld( ... )


def setPalette(palidx):
    global cur_pal_idx

    if palidx != cur_pal_idx:
        cur_pal_idx = palidx
        io.setPalette(palettes[cur_pal_idx])
