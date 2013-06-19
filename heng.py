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
    print "pos:", hvars.pos
    pass


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
    hio.bind("c", hvars.c_api.ClearScreen)

    frame_start = hio.milliSeconds()
    while not hvars.do_quit:
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
