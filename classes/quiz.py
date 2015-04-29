from __future__ import print_function
import os.path as path
from .gestures import Gesture

class Quiz(object):
    
    def __init__(self, fname):
        self.next_index = 0
        self.gestures = list()
        folder = path.abspath(path.dirname(fname))
        self.name = path.basename(fname)
        with open(fname, 'r') as f:
            for raw_line in f:
                line = raw_line.strip()
                if len(line) == 0: continue
                parts = line.split(':')
                gesture_fname = parts[0].strip()
                name = "???"
                if len(parts) > 1:
                    name = parts[1].strip()
                else:
                    dot = gesture_fname.rfind('.')
                    name = gesture_fname[:dot] if dot > 0 else gesture_fname
                gesture_file = path.join(folder, gesture_fname)
                g = Gesture.from_file(gesture_file)
                g.name = name
                self.gestures.append(g)
                # print("{} -> {}".format(gesture_file, name))

    @property
    def done(self):
        return self.next_index >= len(self.gestures)

    def next(self):
        if not self.done:
            g = self.gestures[self.next_index]
            self.next_index += 1
            return g
        else:
            return None