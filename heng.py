#!/usr/bin/env python

import sys
import ctypes

import hvars
import io
import r_main
from utils import wad


def _quit():
    hvars.do_quit = 1

def _showFPS():
    print "%g fps" % hvars.fps_rate

def _mouseMove(delt):
    hvars.c_api.cameraRotatePixels(ctypes.c_float(delt[0]), ctypes.c_float(delt[1]))

_move_dirs = { "right": 0, "forward": 0, "up": 0 }

def _moveForward():
#   _move_dirs["forward"] += { False: -1, True: 1 }
    pass

def _moveRight():
#   _move_dirs["right"] += { False: -1, True: 1 }
    pass

def _moveBack():
#   _move_dirs["forward"] -= { False: -1, True: 1 }
    pass

def _moveLeft():
#   _move_dirs["right"] -= { False: -1, True: 1 }
    pass

def _cameraFly():
#TODO: if up_pressed, ...
    pass
#   rt = ctypes.c_float(vec[0])
#   up = ctypes.c_float(vec[1])
#   fwd = ctypes.c_float(vec[2])
#   hvars.c_api.cameraThrust(rt, up, fwd)

def _debug():
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

        _cameraFly()

        r_main.refresh()
        io.swapBuffer()

        now = io.milliSeconds()
        hvars.frametime = (now - frame_start) / 1000.0
        if hvars.frametime == 0.0:
            hvars.frametime = 0.001
        frame_start = now

    io.shutdown()
