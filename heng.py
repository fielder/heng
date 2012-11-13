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
    hvars.camera.rotatePixels(delt[0], delt[1])

def _moveForward():
    #TODO: ...
    pass

def _moveRight():
    #TODO: ...
    pass

def _moveBack():
    #TODO: ...
    pass

def _moveLeft():
    #TODO: ...
    pass

def _debug():
    print hvars.camera.w
    print hvars.camera.h
    print hvars.camera.dist
    print hvars.camera.fov_x
    print hvars.camera.fov_y
    print hvars.camera.pos
    print hvars.camera.angles
    hvars.camera.findViewVectors()
    print hvars.camera.right
    print hvars.camera.up
    print hvars.camera.forward
    pass


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
    io.bind("x", _debug)
    io.bind("period", _moveForward)
    io.bind("u", _moveRight)
    io.bind("e", _moveBack)
    io.bind("o", _moveLeft)

    frame_start = io.milliSeconds()
    while not hvars.do_quit:
        io.runInput()
        r_main.refresh()
        io.swapBuffer()

        now = io.milliSeconds()
        hvars.frametime = (now - frame_start) / 1000.0
        if hvars.frametime == 0.0:
            hvars.frametime = 0.001
        frame_start = now

    io.shutdown()
