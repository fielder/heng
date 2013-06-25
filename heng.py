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
    print "=" * 64
    print "pos   :", hvars.pos
    print "angles:", hvars.angles
    hvars.c_api.R_SetDebug(1)
    print "-" * 64
    print ""

def _debug2():
    # clip off right: out2.zip
    if sys.argv[2] == "out2.zip":
        pos = (50.12752310306103, 64.0, 285.1381228419543)
        #angles = (1.5707963267948966, 6.2733678301370945, 0.0)
        #angles = (1.533258762115288, 0.559596191420654, 0.0)
        angles = (1.5707963267948966, 0.716675824100113, 0.0)

        # facing opposite so edge goes off bottom
        #angles = (1.5707963267948966, 0.716675824100113, 0.0)
        angles = (1.5707963267948966, 2.586905200690284, 0.0)


    # clip off left: out.zip
    if sys.argv[2] == "out.zip":
        pos = (114.24407283616527, 74.9087274022559, 31.681621420802887)
        angles = (-0.8637828681396933, 3.175953823238353, 0.0)

    r_cam.setCamera(pos, angles)


if __name__ == "__main__":
    if 1:
        sys.argv = [sys.argv[0]] + ["utils/doom.wad", "out.zip"]
    else:
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
