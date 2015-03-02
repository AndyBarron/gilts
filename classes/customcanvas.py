#! /usr/bin/env python
from __future__ import division
import wx
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLUT import *

class BaseGLCanvas(glcanvas.GLCanvas):
    def __init__(self, *args, **kwargs):
        glcanvas.GLCanvas.__init__(self, *args, **kwargs)
        self.init = False
        self.context = glcanvas.GLContext(self)
        
        self.size = self.GetClientSize()
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_erase_background(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def on_size(self, event):
        wx.CallAfter(self.set_viewport) # why?
        event.Skip()
        # w, h = event.GetSize()

    def set_viewport(self):
        size = self.size = self.GetClientSize()
        self.SetCurrent(self.context)
        # glViewport(0, 0, size.width, size.height)
        self.on_gl_size(size.width, size.height)
        
    def on_paint(self, event):
        dc = wx.PaintDC(self)
        self.SetCurrent(self.context)

        if not self.init:
            self.on_gl_init()
            self.on_gl_size(*self.size)
            self.init = True

        self.on_gl_draw()
        self.SwapBuffers()

    def repaint(self, event):
        self.Refresh()

    # overrides!
    def on_gl_init(self): pass
    def on_gl_size(self, w, h): pass
    def on_gl_draw(self): pass

class UpdateGLCanvas(BaseGLCanvas):
    def __init__(self, *args, **kwargs):
        BaseGLCanvas.__init__(self, *args, **kwargs)
        timer = self.timer = wx.Timer(self, wx.ID_ANY)
        timer.Start(1000//60)
        self.Bind(wx.EVT_TIMER, self.repaint)