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

_frame_move = { "right": 0.0, "forward": 0.0, "up": 0.0 }

def _moveForward():
    _frame_move["forward"] += 1.0

def _moveRight():
    _frame_move["right"] += 1.0

def _moveUp():
    _frame_move["up"] += 1.0

def _moveBack():
    _frame_move["forward"] -= 1.0

def _moveLeft():
    _frame_move["right"] -= 1.0

def _moveDown():
    _frame_move["up"] -= 1.0

def _cameraFly():
    rt = ctypes.c_float(_frame_move["right"] * hvars.frametime * hvars.MOVESPEED)
    up = ctypes.c_float(_frame_move["up"] * hvars.frametime * hvars.MOVESPEED)
    fwd = ctypes.c_float(_frame_move["forward"] * hvars.frametime * hvars.MOVESPEED)
    hvars.c_api.cameraThrust(rt, up, fwd)

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
    io.bindContinuous("period", _moveForward)
    io.bindContinuous("u", _moveRight)
    io.bindContinuous("e", _moveBack)
    io.bindContinuous("o", _moveLeft)
    io.bindContinuous("button3", _moveUp)

    frame_start = io.milliSeconds()
    while not hvars.do_quit:
        for direction in _frame_move.keys():
            _frame_move[direction] = 0.0

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
