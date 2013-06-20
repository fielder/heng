import math
import ctypes

import hio
import hvars
from utils import vec

c_vec3 = ctypes.c_float * 3

movespeed = 32.0

_frame_move = { "left":    0.0,
                "forward": 0.0,
                "up":      0.0 }


def init():
    hvars.pos = vec.Vec3()
    hvars.angles = vec.Vec3()
    hvars.left = vec.Vec3()
    hvars.up = vec.Vec3()
    hvars.forward = vec.Vec3()

    hvars.fov_x = math.radians(90.0)
    dist = (hvars.WIDTH / 2.0) / math.tan(hvars.fov_x / 2.0)
    hvars.fov_y = 2.0 * math.atan((hvars.HEIGHT / 2.0) / dist)
    hvars.c_api.R_SetupProjection(ctypes.c_float(hvars.fov_x))

    _calcViewVecs()

    hio.bind("mousemove", _mouseMove)
    hio.bindContinuous(".", _moveForward)
    hio.bindContinuous("u", _moveRight)
    hio.bindContinuous("e", _moveBack)
    hio.bindContinuous("o", _moveLeft)
    hio.bindContinuous("button3", _moveUp)


def update():
    sp = hvars.frametime * movespeed
    thrustCamera(sp * _frame_move["left"],
                 sp * _frame_move["up"],
                 sp * _frame_move["forward"])

    pos = c_vec3(hvars.pos[0], hvars.pos[1], hvars.pos[2])
    angles = c_vec3(hvars.angles[0], hvars.angles[1], hvars.angles[2])

    hvars.c_api.R_SetCamera(pos, angles)


def beginFrame():
    for direction in _frame_move.iterkeys():
        _frame_move[direction] = 0.0


def setCamera(pos, angles):
    hvars.pos = vec.Vec3(pos)
    hvars.angles = vec.Vec3(angles)


def thrustCamera(left, up, forward):
    hvars.pos += hvars.left * left
    hvars.pos += hvars.up * up
    hvars.pos += hvars.forward * forward


def _mouseMove(delt):
    dx = float(delt[0])
    dy = float(delt[1])

    pitch = hvars.angles[hvars.PITCH]
    yaw = hvars.angles[hvars.YAW]
    roll = hvars.angles[hvars.ROLL]

    # using right-handed coordinate system, so positive yaw goes
    # left across the screen and positive roll goes down
    yaw += hvars.fov_x * (-dx / hvars.WIDTH)
    pitch += hvars.fov_y * (dy / hvars.HEIGHT)

    # restrict camera angles
    pitch = min(pitch, math.pi / 2.0)
    pitch = max(pitch, -math.pi / 2.0)

    while yaw >= math.pi * 2.0:
        yaw -= math.pi * 2.0
    while yaw < 0.0:
        yaw += math.pi * 2.0

    hvars.angles = vec.Vec3(pitch, yaw, roll)

    _calcViewVecs()


def _calcViewVecs():
    xform = vec.anglesMatrix(-hvars.angles)

    hvars.left = vec.Vec3(xform[0])
    hvars.up = vec.Vec3(xform[1])
    hvars.forward = vec.Vec3(xform[2])


def _moveForward():
    _frame_move["forward"] += 1.0

def _moveRight():
    _frame_move["left"] -= 1.0

def _moveUp():
    _frame_move["up"] += 1.0

def _moveBack():
    _frame_move["forward"] -= 1.0

def _moveLeft():
    _frame_move["left"] += 1.0

def _moveDown():
    _frame_move["up"] -= 1.0




class ViewState(object):
    pos = None
    angles = None
    name = ""

_vstates = {}

def setState(name, pos, angles):
    vs = ViewState()
    _vstates[name] = vs

    vs.name = name
    vs.pos = vec.Vec3(pos)
    vs.angles = vec.Vec3(angles)
