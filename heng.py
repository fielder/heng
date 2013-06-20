#!/usr/bin/env python

import sys
import ctypes

import hvars
import hio
import r_main
import r_cam
import mapfile
#import console
from utils import wad


def _quit():
    hvars.do_quit = 1


def _showFPS():
    print "%g fps" % hvars.fps_rate


def _debug():
    print "pos   :", hvars.pos
    print "angles:", hvars.angles
    print ""
    hvars.c_api.R_SetDebug(1)

def _debug2():
#   pos = (59.06465037961378, 38.75378027843006, 287.1767908883728)
#   angles = (0.18768782339804116, 0.0, 0.0)
    pos = (50.12752310306103, 127.2341878620401, 285.1381228419543)
    angles = (1.5707963267948966, 6.1702843211911835, 0.0)

    r_cam.setCamera(pos, angles)


if __name__ == "__main__":
    sys.argv = [sys.argv[0]] + ["utils/doom.wad", "out2.zip"]
    if len(sys.argv) != 3:
        print "usage: %s <iwad> <map file>" % sys.argv[0]
        sys.exit(0)

    hvars.iwad = wad.Wad(sys.argv[1])

    hio.init()
    r_main.init()
    r_cam.init()

    # load into the C rendered
    mapfile.load(sys.argv[2])

#   console.write("test line 1\n")
#   console.write("test line 2\n")
#   console.write("two lines\npart of the 2nd\n")

#   hio.bind("backquote", console.toggle)
    hio.bind("escape", _quit)
    hio.bind("f", _showFPS)
    hio.bind("g", hio.toggleGrab)
    hio.bind("x", _debug)
    hio.bind("k", _debug2)
    hio.bind("c", hvars.c_api.ClearScreen)

    frame_start = hio.milliSeconds()
    while not hvars.do_quit:
        hvars.c_api.R_SetDebug(0)

        r_cam.beginFrame()

        hio.runInput()

        r_cam.update()

        r_main.refresh()

        hio.swapBuffer()

        now = hio.milliSeconds()
        hvars.frametime = (now - frame_start) / 1000.0
        if hvars.frametime == 0.0:
            hvars.frametime = 0.001
        frame_start = now

    hio.shutdown()
