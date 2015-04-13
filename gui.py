#! /usr/bin/env python
from __future__ import division, print_function
import json
import time
import math

import wx
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from leap import Leap

import helpers
from classes import *

FILE_WILDCARD = "Hand files (*.hand)|*.hand"

class TeachingFrame(wx.Frame):
    def __init__(self, parent, wxid, lm):
        wx.Frame.__init__(self, parent, wxid,
            title="Teaching Program", size=(800,600))
        frame = self
        panel = wx.Panel(frame, wx.ID_ANY)
        vbox = wx.BoxSizer(wx.HORIZONTAL)
        canvas = self.canvas = LeapCanvas(panel, wx.ID_ANY, lm)
        canvas.capture_static = False
        canvas.record_motion = False
        canvas.record_motion_start = None
        canvas.saved = None
        canvas.motion_frames = None
        canvas.motion_length = 0
        canvas.motion_playback = 0
        vbox.Add(canvas, 1, wx.EXPAND | wx.ALL, border=0)
        controls = self.controls = wx.Panel(panel, wx.ID_ANY)
        cbox = self.cbox = wx.BoxSizer(wx.VERTICAL)
        button_cap = wx.Button(controls, wx.ID_ANY, "Capture static gesture")
        button_record = wx.Button(controls, wx.ID_ANY, "Record motion gesture")
        button_save = wx.Button(controls, wx.ID_ANY, "Save gesture to file")
        button_load = wx.Button(controls, wx.ID_ANY, "Load gesture from file")
        btn_flags = wx.ALIGN_CENTER|wx.ALL|wx.EXPAND
        cbox.Add(button_cap, flag=btn_flags, border=5)
        cbox.Add(button_record, flag=btn_flags, border=5)
        cbox.Add(button_save, flag=btn_flags, border=5)
        cbox.Add(button_load, flag=btn_flags, border=5)
        vbox.Add(controls, flag=wx.ALIGN_RIGHT|wx.RIGHT)
        panel.SetSizer(vbox)
        controls.SetSizer(cbox)
        button_cap.Bind(wx.EVT_BUTTON, lambda _: self.capture_static())
        button_record.Bind(wx.EVT_BUTTON, lambda _: self.record_motion())
        button_save.Bind(wx.EVT_BUTTON, lambda _: self.save_hand())
        button_load.Bind(wx.EVT_BUTTON, lambda _: self.load_hand())
        self.button_record = button_record

    def _add_sidebar_btn(txt, parent, sizer, fn):
        btn = wx.Button(parent, wx.ID_ANY, txt)
        btn_flags = wx.ALIGN_CENTER|wx.ALL|wx.EXPAND
        sizer.Add(btn, flag=btn_flags, border=5)
        btn.Bind(wx.EVT_BUTTON, lambda _: fn())
        return btn

    def capture_static(self):
        self.canvas.capture_static = True

    def record_motion(self):
        new_label = "???"
        recording = self.canvas.record_motion
        if not recording:
            self.canvas.motion_frames = dict()
            self.canvas.record_motion = True
            self.canvas.record_motion_start = time.time()
            self.button_record.SetLabelText("Stop recording")
        else:
            sec = time.time() - self.canvas.record_motion_start
            print(
                "Recording for {:.4} seconds".format(sec)
                )
            self.canvas.motion_length = sec
            self.canvas.record_motion = False
            self.canvas.record_motion_start = None
            self.button_record.SetLabelText("Record motion gesture")

    def save_hand(self):
        if not self.canvas.saved:
            # TODO display message
            return
        fd = wx.FileDialog(self, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
            wildcard=FILE_WILDCARD)
        fd.ShowModal()
        path = fd.GetPath()
        with open(path, 'w') as f:
            json.dump(self.canvas.saved, f, cls=JSONEncoderPlus)

    def load_hand(self):
        fd = wx.FileDialog(self, style=wx.FD_OPEN,
            wildcard=FILE_WILDCARD)
        fd.ShowModal()
        path = fd.GetPath()
        hand_dict = None
        with open(path, 'r') as f:
            hand_dict = json.load(f)
        self.canvas.saved = HandSnapshot(hand_dict)

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
        self.last_time = time.time()

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
                glVertex3f(*joint)
            # for i, bone in enumerate(finger.bone(i) for i in range(4)):
            #     if i == 0: glVertex3f(*bone.prev_joint)
            #     glVertex3f(*bone.next_joint)
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
        # timing
        cur_time = time.time()
        delta = cur_time - self.last_time
        self.last_time = cur_time
        # draw
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        scl = 1/500
        glScalef(scl,scl,scl)
        glTranslatef(0,-375,-500)
        frame = self.lm.frame()
        if self.saved is not None:
            glPushMatrix()
            for hand in frame.hands:
                if hand.is_left == self.saved.is_left:
                    diff = Vec3(hand.palm_position) - self.saved.palm_position
                    glTranslatef(*(diff))
                    break
            glColor3f(0,0.5,1)
            self.draw_hand_snapshot(self.saved)
            glPopMatrix()
        if not self.record_motion and self.motion_frames is not None \
                and len(self.motion_frames) > 0:
            self.motion_playback += delta
            while self.motion_playback >= self.motion_length:
                self.motion_playback -= self.motion_length
            # percent = self.motion_playback / self.motion_length
            # idx = math.floor( len(self.motion_frames) * percent)
            # self.draw_hand_snapshot(self.motion_frames[int(idx)])
            get_dif = lambda t: abs(self.motion_playback - t)
            ts = min(self.motion_frames, key=get_dif)
            snap = self.motion_frames[ts]
            glColor3f(1,1,0)
            self.draw_hand_snapshot(snap)
        for hand in frame.hands:
            if not self.saved or hand.is_left != self.saved.is_left:
                glColor3f(1,1,1)
            else:
                match = HandSnapshot(hand).match_joint_offsets(self.saved, 45)
                color = (0,1,0) if match else (1,0,0)
                glColor3f(*color)
            self.draw_hand(hand)
        glPopMatrix()
        if self.capture_static:
            self.capture_static = False
            if len(frame.hands) > 0:
                self.saved = frame.hands[0]
                self.saved = HandSnapshot(self.saved)
                print(json.dumps(self.saved, cls=JSONEncoderPlus))
                # print(len(list(saved.iter_joints())))
            else:
                self.saved = None
        if self.record_motion and len(frame.hands) > 0:
            key = cur_time - self.record_motion_start
            snap = HandSnapshot(frame.hands[0])
            self.motion_frames[key] = snap