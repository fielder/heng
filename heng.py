#!/usr/bin/env python

import sys
import ctypes

import hvars
import io
import r_main
import r_cam
#import console
from utils import wad


def _quit():
    hvars.do_quit = 1


def _showFPS():
    print "%g fps" % hvars.fps_rate


def _debug():
    pass


def _loadMap(path):
    return
    w = wad.Wad(path)
    #...
    w.close()
    print "Loaded \"%s\"" % path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "usage: %s <iwad> <map file>" % sys.argv[0]
        sys.exit(0)

    hvars.iwad = wad.Wad(sys.argv[1])

    io.init()
    r_main.init()
    r_cam.init()

    _loadMap(sys.argv[2])

#   console.write("test line 1\n")
#   console.write("test line 2\n")
#   console.write("two lines\npart of the 2nd\n")

#   io.bind("backquote", console.toggle)
    io.bind("escape", _quit)
    io.bind("f", _showFPS)
    io.bind("g", io.toggleGrab)
    io.bind("x", _debug)

    frame_start = io.milliSeconds()
    while not hvars.do_quit:
        r_cam.beginFrame()

        io.runInput()

        r_cam.update()

        r_main.refresh()

        io.swapBuffer()

        now = io.milliSeconds()
        hvars.frametime = (now - frame_start) / 1000.0
        if hvars.frametime == 0.0:
            hvars.frametime = 0.001
        frame_start = now

    io.shutdown()
