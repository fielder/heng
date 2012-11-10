import ctypes

import hvars
import cdefs
import io

RENDER_SO = "./render.so"

palettes = []
cur_pal_idx = -1
c_api = None


class Camera(object):
    fov_x = 90.0
    pos = (0.0, 0.0, 0.0)
    angles = (0.0, 0.0, 0.0)


def init():
    global palettes
    global c_api

    c_api = ctypes.cdll.LoadLibrary(RENDER_SO)
    print "Loaded %s" % RENDER_SO

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
    print "Read %d palettes" % len(palettes)

    setPalette(0)

    hvars.camera = Camera()


PLAYA1 = None

def refresh():
    # 2D drawing
    global PLAYA1

    if not PLAYA1:
        PLAYA1 = hvars.iwad.readLump("PLAYA1")

    c_api.drawPalette()
    c_api.drawSprite(PLAYA1, 200, 50)

    # 3D drawing
    c_api.setCamera(ctypes.c_float(hvars.camera.fov_x),
                    cdefs.Vec3(*hvars.camera.pos),
                    cdefs.Vec3(*hvars.camera.angles))
    #...


def setPalette(palidx):
    global cur_pal_idx

    if palidx != cur_pal_idx:
        cur_pal_idx = palidx
        io.setPalette(palettes[cur_pal_idx])
