import math

import hvars
from utils import vec


class Camera(object):
    w = 0.0
    h = 0.0
    fov_x = 0.0

    pos = (0.0, 0.0, 0.0)
    angles = (0.0, 0.0, 0.0)

    right = (0.0, 0.0, 0.0)
    up = (0.0, 0.0, 0.0)
    forward = (0.0, 0.0, 0.0)

    def __init__(self, w, h, fov_x):
        self.w = float(w)
        self.h = float(h)
        self.fov_x = float(fov_x)

    def _centerX(self):
        return self.w / 2.0 - 0.5

    def _centerY(self):
        return self.h / 2.0 - 0.5

    def _dist(self):
        return (self.w / 2.0) / math.tan(self.fov_x / 2.0)

    def _fov_y(self):
        return 2.0 * math.atan((self.h / 2.0) / self.dist)

    center_x = property(_centerX)
    center_y = property(_centerY)
    dist = property(_dist)
    fov_y = property(_fov_y)

    def restrictAngles(self):
        pitch, yaw, roll = self.angles

        if pitch > math.pi / 2.0:
            pitch = math.pi / 2.0
        if pitch < -math.pi / 2.0:
            pitch = -math.pi / 2.0

        while roll >= math.pi * 2.0:
            roll -= math.pi * 2.0
        while roll < 0.0:
            roll += math.pi * 2.0

        while yaw >= math.pi * 2.0:
            yaw -= math.pi * 2.0
        while yaw < 0.0:
            yaw += math.pi * 2.0

        self.angles = (pitch, yaw, roll)

    def findViewVectors(self):
        """
        Set up the right, up, forward vectors.
        """

        xform = vec.anglesMatrix(vec.vecScale(self.angles, -1.0), "xyz")

        self.right = xform[0]
        self.up = xform[1]
        self.forward = xform[2]

        # We're looking down the -z axis, and our projection calculation
        # assumes greater z is further away. So negate z values making
        # positive z objects behind the camera.
        self.forward = vec.vecScale(self.forward, -1.0)

    def rotate(self, angles):
        self.angles = vec.vecAdd(self.angles, angles)
        self.restrictAngles()

    def rotatePixels(self, dx, dy):
        """
        Rotate the camera based on pixels, in screen coordinates. Used
        by the mouse to control the camera.
        """

        pitch = self.fov_y * (-dy / self.h)
        yaw = self.fov_x * (-dx / self.w)
        roll = 0.0

        self.rotate((pitch, yaw, roll))

    def thrust(self, v):
        self.pos = vec.vecAdd(self.pos, v)


def init():
    hvars.camera = Camera(hvars.WIDTH, hvars.HEIGHT, math.radians(90.0))
