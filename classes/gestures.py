from .handsnapshot import HandSnapshot

class Gesture(object):

    @staticmethod
    def from_dict(d):
        if d["type"] == "static":
            return StaticGesture(HandSnapshot(d["data"]))
        elif d["type"] == "motion":
            dct = {t: HandSnapshot(s) for t, s in d["data"].iteritems()}
            return StaticGesture(dct)
        else:
            raise TypeError("Invalid args to Gesture constructor")

    def match(self, frames):
        raise NotImplementedError("Gesture class is abstract")

    def _custom_json(self):
        raise NotImplementedError("Gesture class is abstract")


class StaticGesture(Gesture):

    def __init__(self, snapshot):
        self.snapshot = snapshot

    def match(self, frames):
        last = frames[max(frames)]
        return self.snapshot.match_joint_offsets(last)

    def _custom_json(self):
        return {
            "type": "static",
            "data": self.snapshot._custom_json()
        }

class MotionGesture(Gesture):

    def __init__(self, snapshots):
        self.snapshots = snapshots
        self.length = max(snapshots) - min(snapshots)

    def nearest_snapshot(time):
        ts = time % self.length
        return min(self.snapshots, key=lambda t: abs(ts - t))

    def match(self, frames):
        for time, snap in frames.iteritems():
            saved = self.nearest_snapshot(time)
            if not saved.match_joint_offsets(snap):
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