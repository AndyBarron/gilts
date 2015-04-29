import json

from .handsnapshot import HandSnapshot

class Gesture(object):

    @staticmethod
    def from_dict(d):
        if d["type"] == "static":
            return StaticGesture(HandSnapshot(d["data"]))
        elif d["type"] == "motion":
            dct = {float(t): HandSnapshot(s) for t, s in d["data"].iteritems()}
            return MotionGesture(dct)
        else:
            raise TypeError("Invalid args to Gesture constructor")

    @staticmethod
    def from_file(fname):
        with open(fname, 'r') as f:
            return Gesture.from_dict(json.load(f))

    def match(self, frames):
        raise NotImplementedError("Gesture class is abstract")

    def _custom_json(self):
        raise NotImplementedError("Gesture class is abstract")

    @property
    def is_left(self):
        raise NotImplementedError("Gesture class is abstract")


class StaticGesture(Gesture):

    def __init__(self, snapshot):
        self.snapshot = snapshot

    def match(self, frames):
        if not frames: return False
        last = frames[max(frames)]
        return self.snapshot.match_joint_offsets(last)

    def _custom_json(self):
        return {
            "type": "static",
            "data": self.snapshot._custom_json()
        }

    @property
    def is_left(self):
        return self.snapshot.is_left

class MotionGesture(Gesture):

    def __init__(self, snapshots):
        self.snapshots = snapshots.copy()
        self.length = max(snapshots) - min(snapshots)

    def nearest_snapshot(self, time):
        ts = time % self.length
        return self.snapshots[min(self.snapshots, key=lambda t: abs(ts - t))]

    def match(self, frames):
        if not frames: return False
        frames_length = max(frames) - min(frames)
        if not (0.5*self.length < frames_length < 1.5*self.length): return False

        start = min(self.snapshots.iteritems())[1]
        first_frame = min(frames.iteritems())[1]
        for time, snap in frames.iteritems():
            saved = self.nearest_snapshot(time)
            self_offset = saved.palm_position - start.palm_position
            other_offset = snap.palm_position - first_frame.palm_position
            if not saved.match_joint_offsets(snap,
                    self_offset=self_offset, other_offset=other_offset,
                    threshold=65): # TODO no worky :(
                return False
        return True
        # for time, snap in self.snapshots.iteritems():
        #     closest_time = min(frames, key=lambda t: abs(time - t))
        #     frame = frames[closest_time]
        #     if not snap.match_joint_offsets(frame):
        #         return False
        # return True

    def _custom_json(self):
        return {
            "type": "motion",
            "data": { time : gesture._custom_json() for time, gesture in
                self.snapshots.iteritems() }
        }

    @property
    def is_left(self):
        return self.snapshots[min(self.snapshots)].is_left