import itertools
from leap import Leap

def _finger_joints(finger):
    for i in range(4):
        bone = finger.bone(i)
        if i == 0: yield bone.prev_joint
        yield bone.next_joint

Leap.Finger.iter_joints = _finger_joints

def _hand_joints(hand):
    by_finger = [ _finger_joints(f) for f in hand.fingers ]
    return itertools.chain.from_iterable(by_finger)

Leap.Hand.iter_joints = _hand_joints

def _hand_match(hand, other, tolerance):
    pa = hand.palm_position
    pb = other.palm_position
    for ja, jb in itertools.izip(hand.iter_joints(), other.iter_joints()):
        ta = ja - pa
        tb = jb - pb
        if (ta - tb).magnitude > tolerance:
            return False
    return True

Leap.Hand.match = _hand_match

def _vector_iter(vec):
    yield vec.x
    yield vec.y
    yield vec.z

Leap.Vector.__iter__ = _vector_iter