
class Gesture(object):

    def match(self, frames):
        raise NotImplementedError("Gesture class is abstract")

    def _custom_json(self):
        raise NotImplementedError("Gesture class is abstract")


class StaticGesture(Gesture):

    def __init__(self, snapshot):
        self.snapshot = snapshot

    def match(self, frames):
        last = frames[max(frames)]
        return snapshot.match_joint_offsets(last)

    def _custom_json(self):
        return {
            "type": "static",
            "data": self.snapshot._custom_json()
        }