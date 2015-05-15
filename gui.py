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

QUIZ_TIME = 5
SECONDS_TO_RECORD = 10
HAND_FILE_WILDCARD = "Hand files (*.hand)|*.hand"
QUIZ_FILE_WILDCARD = "Quiz files (*.txt)|*.txt"

def show_modal(title, msg):
    wx.MessageDialog(None, msg, title, style=wx.OK|wx.CENTRE).ShowModal()

class TeachingFrame(wx.Frame):
    def __init__(self, parent, wxid, lm):
        wx.Frame.__init__(self, parent, wxid,
            title="Teaching Program", size=(800,600))
        frame = self
        panel = wx.Panel(frame, wx.ID_ANY)
        vbox = wx.BoxSizer(wx.HORIZONTAL)
        canvas = self.canvas = LeapCanvas(panel, wx.ID_ANY, lm)
        vbox.Add(canvas, 1, wx.EXPAND | wx.ALL, border=0)
        controls = wx.Panel(panel, wx.ID_ANY)
        cbox = wx.BoxSizer(wx.VERTICAL)
        self.btn_cap = self._add_sidebar_btn("Capture static gesture", controls,
            cbox, self.capture_static)
        self.btn_rec = self._add_sidebar_btn("Record motion gesture", controls,
            cbox, self.record_motion)
        self.btn_save = self._add_sidebar_btn("Save gesture to file", controls,
            cbox, self.save_hand)
        self.btn_clear = self._add_sidebar_btn("Clear gesture", controls,
            cbox, self.clear_gesture)
        self.btn_load = self._add_sidebar_btn("Load gesture from file", controls,
            cbox, self.load_hand)
        self.btn_quiz = self._add_sidebar_btn("Load gesture quiz file", controls,
            cbox, self.load_quiz)
        self.txt_quiz = self._add_sidebar_txt("", controls, cbox)
        vbox.Add(controls, flag=wx.ALIGN_RIGHT|wx.RIGHT)
        panel.SetSizer(vbox)
        controls.SetSizer(cbox)
        self.btn_rec._msg_start_record = self.btn_rec.GetLabelText()
        self.btn_rec._msg_stop_record = "Stop recording"
        self.recording = False

    def _add_sidebar_btn(self, txt, parent, sizer, fn=None):
        btn = wx.Button(parent, wx.ID_ANY, txt)
        btn_flags = wx.ALIGN_CENTER|wx.ALL|wx.EXPAND
        sizer.Add(btn, flag=btn_flags, border=5)
        if fn is not None:
            btn.Bind(wx.EVT_BUTTON, lambda _: fn())
        return btn

    def _add_sidebar_txt(self, txt, parent, sizer):
        txt = wx.StaticText(parent, wx.ID_ANY, txt)
        txt.Wrap(90)
        txt_flags = wx.ALIGN_CENTER|wx.ALL|wx.EXPAND
        sizer.Add(txt, flag=txt_flags, border=5)
        return txt

    def clear_gesture(self):
        self.canvas.saved = None
        self.canvas.quiz = None

    def capture_static(self):
        if self.recording: return
        self.canvas.saved = None
        snaps = self.canvas.snapshots
        if len(snaps) > 0:
            self.canvas.saved = StaticGesture(snaps[max(snaps)])

    # TODO disable save/load buttons
    def record_motion(self):
        if not self.recording:
            self.canvas.saved = None
            self.canvas.snapshots.clear()
            self.btn_rec.SetLabelText(self.btn_rec._msg_stop_record)
            self.btn_cap.Disable()
            self.btn_quiz.Disable()
            self.btn_save.Disable()
            self.btn_load.Disable()
        else:
            if len(self.canvas.snapshots) > 0:
                self.canvas.saved = MotionGesture(self.canvas.snapshots)
                self.canvas.playback_timer = 0
                self.canvas.snapshots.clear()
            self.btn_rec.SetLabelText(self.btn_rec._msg_start_record)
            self.btn_cap.Enable()
            self.btn_quiz.Enable()
            self.btn_save.Enable()
            self.btn_load.Enable()
        self.recording = not self.recording

    def save_hand(self):
        if self.recording: return
        if not self.canvas.saved:
            # TODO display message
            return
        fd = wx.FileDialog(self, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
            wildcard=HAND_FILE_WILDCARD)
        fd.ShowModal()
        path = fd.GetPath()
        with open(path, 'w') as f:
            json.dump(self.canvas.saved, f, cls=JSONEncoderPlus)

    def load_quiz(self):
        if self.recording: return
        fd = wx.FileDialog(self, style=wx.FD_OPEN,
            wildcard=QUIZ_FILE_WILDCARD)
        fd.ShowModal()
        path = fd.GetPath()
        if not path: return
        q = Quiz(path)
        self.canvas.quiz = q
        self.canvas.saved = None # q.gestures[0]
        msg = "Get ready!"
        title = "Beginning quiz: " + q.name
        # show_modal(title, msg)


    def load_hand(self):
        if self.recording: return
        fd = wx.FileDialog(self, style=wx.FD_OPEN,
            wildcard=HAND_FILE_WILDCARD)
        fd.ShowModal()
        path = fd.GetPath()
        if not path: return
        hand_dict = None
        with open(path, 'r') as f:
            hand_dict = json.load(f)
        self.canvas.saved = Gesture.from_dict(hand_dict)

class LeapCanvas(UpdateGLCanvas):
    def __init__(self, parent, wxid, controller, *args, **kwargs):
        UpdateGLCanvas.__init__(self, parent, wxid, *args, **kwargs)
        self.matching = False
        self.quiz = None
        self.quiz_timer = 0
        self.lm = controller
        self.last_frame = None
        self.saved = None
        self.snapshots = dict()
        self.playback_timer = 0
        self.playback_offset = None
        # init stuff
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

    def update(self, delta):

        #### debug
        # if not hasattr(self, "q"):
        #     self.q = 0
        # self.q += delta
        # if self.q >= 1:
        #     self.q -= 1
        #     k = self.snapshots.keys()
        #     if len(k) > 0:
        #         print(min(k), max(k))
        #     else:
        #         print("-")
        ####

        # playback!
        if isinstance(self.saved, MotionGesture):
            self.playback_timer += delta
            self.playback_timer %= self.saved.length

        # capturing/saving
        frame = self.last_frame = self.lm.frame()
        if len(frame.hands) == 1:
            hand = frame.hands[0]
            snap = HandSnapshot(hand)
            if len(self.snapshots) == 0:
                self.snapshots[0.0] = snap
            else:
                new_ts = max(self.snapshots) + delta
                self.snapshots[new_ts] = snap
                sec_limit = SECONDS_TO_RECORD if not isinstance(self.saved, MotionGesture) \
                    else self.saved.length
                if new_ts > sec_limit:
                    diff = new_ts - sec_limit
                    self.snapshots = {t-diff: s for t, s in
                        self.snapshots.iteritems() if t-diff >= 0}
                    first = min(self.snapshots)
                    if first > 0:
                        self.snapshots = {t-first: s for t, s in
                            self.snapshots.iteritems()}
        else:
            self.snapshots.clear()

        # actually do matching
        self.matching = self.saved and self.saved.match(self.snapshots)
        if self.quiz and (self.matching or self.saved is None):
            self.saved = None
            if self.quiz.done:
                show_modal("Good job!", "You finished the quiz: " + self.quiz.name)
                self.quiz = None
            else:
                self.saved = self.quiz.next()
                got_right = self.matching
                title = "Good job!" if got_right else ("Starting quiz: " +
                    self.quiz.name)
                msg = "Next gesture: " + self.saved.name
                show_modal(title, msg)
                


    def on_gl_draw(self):

        # timing
        cur_time = time.time()
        delta = cur_time - self.last_time
        self.last_time = cur_time
        self.update(delta)
        # draw
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        scl = 1/500
        glScalef(scl,scl,scl)
        glTranslatef(0,-375,-500)
        frame = self.last_frame
        if isinstance(self.saved, StaticGesture):
            snap = self.saved.snapshot
            glPushMatrix()
            if len(frame.hands) == 1:
                hand = frame.hands[0]
                if hand.is_left == snap.is_left:
                    diff = Vec3(hand.palm_position) - snap.palm_position
                    glTranslatef(*diff)
            glColor3f(0,0.5,1)
            assert isinstance(snap, HandSnapshot)
            self.draw_hand_snapshot(snap)
            glPopMatrix()
        elif isinstance(self.saved, MotionGesture):
            snap = self.saved.nearest_snapshot(self.playback_timer)
            assert isinstance(snap, HandSnapshot)
            is_first = snap == min(self.saved.snapshots.iteritems())[1]
            if is_first:
                if len(frame.hands) == 1:
                    hand = frame.hands[0]
                    diff = Vec3(hand.palm_position) - snap.palm_position
                    self.playback_offset = diff
                else:
                    self.playback_offset = None
            glPushMatrix()
            glColor3f(1,1,0)
            if self.playback_offset:
                glTranslatef(*self.playback_offset)
            self.draw_hand_snapshot(snap)
            glPopMatrix()

        if self.saved:
            color = (0,1,0) if self.matching else (1,0,0)
            glColor3f(*color)
        else:
            glColor3f(1,1,1)

        for hand in frame.hands:
            self.draw_hand(hand)
        glPopMatrix()