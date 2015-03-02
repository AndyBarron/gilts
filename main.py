#!/usr/bin/env python
from leap import Leap
import wx

import gui

if __name__ == '__main__':
    app = wx.App(False)
    lm = Leap.Controller()
    frame = gui.TeachingFrame(None, wx.ID_ANY, lm)
    frame.Show(True)
    app.MainLoop()