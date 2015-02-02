#! /usr/bin/env python
from __future__ import division, print_function
import wx
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from leap import Leap

from classes import *

do_save = False
saved = None

def save_hand():
    global do_save
    do_save = True

def main():
    app = wx.App(False)
    lm = Leap.Controller()
    frame = wx.Frame(None, wx.ID_ANY, "App")
    panel = wx.Panel(frame, wx.ID_ANY)
    vbox = wx.BoxSizer(wx.VERTICAL)
    canvas = LeapCanvas(panel, wx.ID_ANY, lm)
    vbox.Add(canvas, 1, wx.EXPAND | wx.ALL, border=0)
    # button = wx.Button(panel, wx.ID_ANY, "Button!")
    # vbox.Add(button, 0, wx.EXPAND | wx.ALL, 0)
    controls = wx.Panel(panel, wx.ID_ANY)
    cbox = wx.BoxSizer(wx.HORIZONTAL)
    button = wx.Button(controls, wx.ID_ANY, "Save Gesture")
    cbox.Add(button, flag=wx.ALL, border=5)
    vbox.Add(controls, flag=wx.ALIGN_RIGHT|wx.RIGHT)
    panel.SetSizer(vbox)
    controls.SetSizer(cbox)
    button.Bind(wx.EVT_BUTTON, lambda self: save_hand())
    frame.Show(True)
    app.MainLoop()

def glVertexVector(v):
    glVertex3f(v.x, v.y, v.z)

class LeapCanvas(UpdateGLCanvas):
    def __init__(self, parent, wxid, controller, *args, **kwargs):
        UpdateGLCanvas.__init__(self, parent, wxid, *args, **kwargs)
        lm = self.lm = controller
        while not self.lm.is_connected: pass

    def on_gl_init(self):
        # step 1
        glClearColor(0.0, 0.0, 0.2, 1.0)
        glClearDepth(1.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glShadeModel(GL_SMOOTH)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    def on_gl_size(self, w, h):
        # step 2
        w, h = self.size
        aspect = w/h
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, aspect, 0.1, 1000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def draw_hand(self, hand):
        glPushMatrix()
        pos = hand.palm_position
        glTranslatef(pos.x, pos.y, pos.z)
        # glutSolidSphere(100, 32, 32)
        for finger in hand.fingers:
            glBegin(GL_LINE_STRIP)
            for i, bone in enumerate(finger.bone(i) for i in range(4)):
                if i == 0: glVertexVector(bone.prev_joint)
                glVertexVector(bone.next_joint)
            glEnd()
        glPopMatrix()

    def on_gl_draw(self):
        global do_save
        global saved
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        scl = 1/500
        glScalef(scl,scl,scl)
        glTranslatef(0,-375,-500)
        frame = self.lm.frame()
        if saved is not None:
            glColor3f(0,1,1)
            self.draw_hand(saved)
        for hand in frame.hands:
            glColor3f(1,1,1)
            self.draw_hand(hand)
        glPopMatrix()
        if do_save:
            do_save = False
            if len(frame.hands) > 0:
                saved = frame.hands[0]
            else:
                saved = None
        

if __name__ == "__main__":
    main()