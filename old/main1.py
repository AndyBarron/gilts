#! /usr/bin/env python
from __future__ import division, print_function
import json
import time

import wx
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from leap import Leap

import helpers
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
    vbox = wx.BoxSizer(wx.HORIZONTAL)
    canvas = LeapCanvas(panel, wx.ID_ANY, lm)
    vbox.Add(canvas, 1, wx.EXPAND | wx.ALL, border=0)
    controls = wx.Panel(panel, wx.ID_ANY)
    cbox = wx.BoxSizer(wx.VERTICAL)
    button_cap = wx.Button(controls, wx.ID_ANY, "Capture gesture")
    button_save = wx.Button(controls, wx.ID_ANY, "Save gesture to file")
    button_load = wx.Button(controls, wx.ID_ANY, "Load gesture to file")
    btn_flags = wx.ALIGN_CENTER|wx.ALL|wx.EXPAND
    cbox.Add(button_cap, flag=btn_flags, border=5)
    cbox.Add(button_save, flag=btn_flags, border=5)
    cbox.Add(button_load, flag=btn_flags, border=5)
    vbox.Add(controls, flag=wx.ALIGN_RIGHT|wx.RIGHT)
    panel.SetSizer(vbox)
    controls.SetSizer(cbox)
    button_cap.Bind(wx.EVT_BUTTON, lambda self: save_hand())
    frame.Show(True)
    app.MainLoop()

def glVertexVector(v):
    glVertex3f(v.x, v.y, v.z)

class LeapCanvas(UpdateGLCanvas):
    def __init__(self, parent, wxid, controller, *args, **kwargs):
        UpdateGLCanvas.__init__(self, parent, wxid, *args, **kwargs)
        self.lm = controller
        wait_timer = 0
        wait_interval = 0.1
        wait_max = 2
        while not self.lm.is_connected:
            if wait_timer >= wait_max:
                print("Error: Leap Motion not connected.")
                exit()
            time.sleep(wait_interval)
            wait_timer += wait_interval

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
        # glTranslatef(pos.x, pos.y, pos.z)
        # glutSolidSphere(100, 32, 32)
        for finger in hand.fingers:
            glBegin(GL_LINE_STRIP)
            for joint in finger.iter_joints():
                glVertexVector(joint)
            # for i, bone in enumerate(finger.bone(i) for i in range(4)):
            #     if i == 0: glVertexVector(bone.prev_joint)
            #     glVertexVector(bone.next_joint)
            glEnd()
        glPopMatrix()

    def draw_hand_snapshot(self, hand):
        glPushMatrix()
        glTranslatef(*hand.palm_position)
        for finger in hand.joint_offsets:
            glBegin(GL_LINE_STRIP)
            for joint in finger:
                glVertex3f(*joint)
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
            glPushMatrix()
            for hand in frame.hands:
                if hand.is_left == saved.is_left:
                    diff = Vec3(hand.palm_position) - saved.palm_position
                    glTranslatef(*(diff))
                    break
            glColor3f(0,0.5,1)
            self.draw_hand_snapshot(saved)
            glPopMatrix()
        for hand in frame.hands:
            if not saved or hand.is_left != saved.is_left:
                glColor3f(1,1,1)
            else:
                match = HandSnapshot(hand).match_joint_offsets(saved, 45)
                color = (0,1,0) if match else (1,0,0)
                glColor3f(*color)
            self.draw_hand(hand)
        glPopMatrix()
        if do_save:
            do_save = False
            if len(frame.hands) > 0:
                saved = frame.hands[0]
                saved = HandSnapshot(saved)
                print(json.dumps(saved, cls=JSONEncoderPlus))
                # print(len(list(saved.iter_joints())))
            else:
                saved = None
        

if __name__ == "__main__":
    main()