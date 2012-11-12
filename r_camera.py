import hvars


class Camera(object):
    fov_x = 90.0

    pos = (0.0, 0.0, 0.0)
    angles = (0.0, 0.0, 0.0)

    right = (0.0, 0.0, 0.0)
    up = (0.0, 0.0, 0.0)
    forward = (0.0, 0.0, 0.0)

    def restrictAngles(self):
        #TODO: ...
        pass

    def findAxis(self):
        """
        Set up the right, up, forward vectors.
        """

        #TODO: ...

    def rotate(self, roll, pitch, yaw):
        pass

    def thrust(self, forward, right, up):
        #TODO: ...
        pass


def init():
    hvars.camera = Camera()
