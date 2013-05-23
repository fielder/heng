#!/usr/bin/env python

import sys
import os
import math
import random

from OpenGL import GL

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL

sys.path.append(os.path.relpath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import vec

appname = "Poly Viewer"
win = None
last_path = ""

polys = []


def _loadPolys(path):
    ret = []
    for line in open(path, "rt").read().strip().split("\n"):
        p = vec.Poly3D.newFromString(line)
        p.rgb = (random.random(), random.random(), random.random())
        ret.append(p)
    return ret


def gluPerspective(fovx, aspect, znear, zfar):
    xmax = znear * math.tan(math.radians(fovx) / 2.0)
    xmin = -xmax

    ymax = xmax / aspect
    ymin = xmin / aspect

    GL.glFrustum(xmin, xmax, ymin, ymax, znear, zfar)


class PolyViewWidget(QtOpenGL.QGLWidget):
    def __init__(self):
        super(PolyViewWidget, self).__init__()

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self._last_mouse_pos = {}
        self.move_speed = 64.0

        self.fovx = 90.0
        self.znear = 4.0
        self.zfar = 4096.0

        self.angles = vec.Vec3()
        self.pos = vec.Vec3()

    @property
    def dist(self):
        return (self.width() / 2.0) / math.tan(math.radians(self.fovx) / 2.0)

    @property
    def fovy(self):
	    return math.degrees(2.0 * math.atan((self.height() / 2.0) / self.dist))

    @property
    def vecs(self):
        m = GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX)

        x = vec.Vec3(m[0][0], m[1][0], m[2][0])
        y = vec.Vec3(m[0][1], m[1][1], m[2][1])
        z = vec.Vec3(m[0][2], m[1][2], m[2][2])

        return (x, y, z)

    def paintGL(self):
        w, h = self.width(), self.height()

        GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT | GL.GL_COLOR_BUFFER_BIT)
        GL.glViewport(0, 0, w, h)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        gluPerspective(self.fovx, w / float(h), self.znear, self.zfar)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        GL.glRotatef(-self.angles[0], 1.0, 0.0, 0.0)
        GL.glRotatef(-self.angles[1], 0.0, 1.0, 0.0)
        GL.glRotatef(-self.angles[2], 0.0, 0.0, 1.0)

        GL.glTranslatef(-self.pos[0], -self.pos[1], -self.pos[2])

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_ALPHA_TEST)
        GL.glDisable(GL.GL_BLEND)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)

        s = 128.0
        GL.glBegin(GL.GL_LINES)
        GL.glColor4f(1.0, 0.0, 0.0, 1.0)
        GL.glVertex3f(0, 0, 0)
        GL.glVertex3f(s, 4, 4)

        GL.glColor4f(0.0, 1.0, 0.0, 1.0)
        GL.glVertex3f(0, 0, 0)
        GL.glVertex3f(4, s, 4)

        GL.glColor4f(0.0, 0.0, 1.0, 1.0)
        GL.glVertex3f(0, 0, 0)
        GL.glVertex3f(4, 4, s)
        GL.glEnd()

        for p in polys:
            GL.glColor4f(p.rgb[0], p.rgb[1], p.rgb[2], 1.0)
            GL.glBegin(GL.GL_POLYGON)
            for v in p:
                GL.glVertex3f(v[0], v[1], v[2])
            GL.glEnd()

#       GL.glFlush()
#       GL.glFinish()

    def resizeGL(self, w, h):
        pass

    def initializeGL(self):
        pass

    def keyPressEvent(self, event):
        k = event.key()

        if k == QtCore.Qt.Key_Left:
            pass
        if k == QtCore.Qt.Key_Right:
            pass
        if k == QtCore.Qt.Key_Up:
            pass
        if k == QtCore.Qt.Key_Down:
            pass
        if k == QtCore.Qt.Key_M:
            print "+++++++++++++++++"
            print self.pos
            m = GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX)
            m = [[round(v) for v in l] for l in m]
            for l in m:
                print l
            print
            print self.vecs
            print "-----------------"

    def wheelEvent(self, event):
        # remember forward is down the -z axis
        x, y, z = self.vecs
        if event.delta() > 0:
            self.pos -= z * self.move_speed
        else:
            self.pos += z * self.move_speed
        self.update()

    def mousePressEvent(self, event):
        b = QtCore.Qt.MiddleButton
        if event.button() == b:
            self._last_mouse_pos[b] = event.pos()

    def mouseMoveEvent(self, event):
        w, h = self.width(), self.height()

        b = QtCore.Qt.MiddleButton
        if (event.buttons() & b) == b:
            delta = event.pos() - self._last_mouse_pos[b]
            self._last_mouse_pos[b] = event.pos()

            rot_yaw = -delta.x() * (self.fovx / w)
            rot_pitch = -delta.y() * (self.fovy / h)
            rot_roll = 0

            pitch = self.angles[0] + rot_pitch
            pitch = max(-90, pitch)
            pitch = min(90, pitch)

            yaw = self.angles[1] + rot_yaw
            while yaw >= 360.0: yaw -= 360.0
            while yaw < 0.0: yaw += 360.0

            roll = self.angles[2] + rot_roll
            while roll >= 360.0: roll -= 360.0
            while roll < 0.0: roll += 360.0

            self.angles = vec.Vec3(pitch, yaw, roll)

            self.update()


def getPath():
    if last_path:
        dir_ = os.path.dirname(last_path)
    else:
        dir_ = os.path.curdir
    return str(QtGui.QFileDialog.getOpenFileName(caption="Open", directory=dir_))

def _loadDoc(path):
    global last_path
    global polys

    try:
        polys = _loadPolys(path)
    except Exception, e:
        QtGui.QErrorMessage(parent=win).showMessage(str(e))
        return False

    last_path = path
    win.setWindowTitle("%s (%s)" % (appname, path))
    win.update()

def _doOpen():
    path = getPath()
    if path:
        _loadDoc(path)

def _doQuit():
    QtGui.QApplication.instance().quit()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    win = QtGui.QMainWindow()
    win.setCentralWidget(PolyViewWidget())
    win.setWindowIcon(QtGui.QIcon(":/trolltech/qmessagebox/images/qtlogo-64.png"))
    win.show()
    win.resize(512, 384)
    win.setWindowTitle("%s (%s)" % (appname, "No Name"))

    m = win.menuBar().addMenu("&File")
    a = m.addAction("&Open", _doOpen)
    a.setShortcut(QtGui.QKeySequence.Open)
    m.addSeparator()
    a = m.addAction("E&xit", _doQuit)
    a.setShortcut(QtGui.QKeySequence.Quit)

    if len(sys.argv) > 1:
        _loadDoc(sys.argv[1])

    sys.exit(app.exec_())

