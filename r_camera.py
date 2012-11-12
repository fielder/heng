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
        p, y, r = self.angles

        if p > math.pi / 2.0:
            p = math.pi / 2.0
        if p < -math.pi / 2.0:
            p = -math.pi / 2.0

        while y >= math.pi * 2.0:
            y -= math.pi * 2.0
        while y < 0.0:
            y += math.pi * 2.0

        self.angles = (p, y, r)

    def findAxis(self):
        """
        Set up the right, up, forward vectors.
        """

        #TODO: ...

    def rotate(self, angles):
        self.angles = vec.vecAdd(self.angles, angles)
        self.restrictAngles()

    def rotatePixels(self, dx, dy):
        p = -self.fov_y * (dy / self.h)
        y = -self.fov_x * (dx / self.w)
        r = 0.0
        self.rotate((p, y, r))
        self.restrictAngles()

    def thrust(self, forward, right, up):
        #TODO: ...
        pass


def init():
    hvars.camera = Camera(hvars.WIDTH, hvars.HEIGHT, math.radians(90.0))
