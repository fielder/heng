#!/usr/bin/env python

import sys

import hvars
import io
import r_main
from utils import wad


def _quit():
    hvars.do_quit = 1

def _showFPS():
    print "%g fps" % hvars.fps_rate

def _mouseMove(delt):
    print delt


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "usage: %s <iwad> <hwa map file>" % sys.argv[0]
        sys.exit(0)

    hvars.iwad = wad.Wad(sys.argv[1])
    hvars.hwa = None

    io.init()
    r_main.init()

    io.bind("escape", _quit)
    io.bind("f", _showFPS)
    io.bind("mousemove", _mouseMove)
    io.bind("g", io.toggleGrab)

    while not hvars.do_quit:
        io.runInput()
        r_main.refresh()
        io.swapBuffer()

    io.shutdown()
