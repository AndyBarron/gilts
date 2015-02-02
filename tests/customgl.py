#! /usr/bin/env python
import wx
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLUT import *

def main():
    app = wx.App(False)
    frame = wx.Frame(None, wx.ID_ANY, "OpenGL")
    canvas = BaseGLCanvas(frame, wx.ID_ANY)
    frame.Show(True)
    app.MainLoop()

class BaseGLCanvas(glcanvas.GLCanvas):
    def __init__(self, *args, **kwargs):
        glcanvas.GLCanvas.__init__(self, *args, **kwargs)
        self.init = False
        self.context = glcanvas.GLContext(self)
        
        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def OnSize(self, event):
        wx.CallAfter(self.DoSetViewport)
        event.Skip()

    def DoSetViewport(self):
        print "Setting viewport"
        size = self.size = self.GetClientSize()
        self.SetCurrent(self.context)
        glViewport(0, 0, size.width, size.height)
        
    def OnPaint(self, event):
        print "Painting"
        dc = wx.PaintDC(self)
        self.SetCurrent(self.context)
        if not self.init:
            self.OnInitGL()
            self.init = True
        self.OnDrawGL()
        self.SwapBuffers()

    # overrides!
    def OnInitGL(self): pass
    def OnDrawGL(self): pass

if __name__ == "__main__":
    main()