import itertools

from vec3 import *

class HandSnapshot(object):
    __slots__ = [
        "is_left",
        "palm_normal",
        "palm_position",
        "joint_offsets",
        # "wrist_offset", # listed in API but doesn't exist???
    ]

    def __init__(self, leap_hand=None):
        if not leap_hand:
            self.is_left = False
            self.palm_normal = Vec3(0,-1,0)
            self.palm_position = Vec3(0,50,0)
            self.joint_offsets = list()
            for i in range(5):
                self.joint_offsets.append([Vec3()] * (4 if i == 0 else 5))
        elif type(leap_hand) == dict:
            self.capture_dict(leap_hand)
        else:
            self.capture_leap_hand(leap_hand)

    def capture_dict(self, d):
        self.is_left = d['is_left']
        self.palm_normal = Vec3(d['palm_normal'])
        self.palm_position = Vec3(d['palm_position'])
        self.joint_offsets = list()
        for finger in d['joint_offsets']:
            joints = list()
            self.joint_offsets.append(joints)
            for joint in finger:
                joints.append(Vec3(joint))

    def capture_leap_hand(self,leap_hand):
        origin = self.palm_position = Vec3(leap_hand.palm_position)
        self.is_left = leap_hand.is_left
        self.palm_normal = Vec3(leap_hand.palm_normal)
        # self.wrist_offset = Vec3(leap_hand.wrist_position) - origin
        self.joint_offsets = list()
        for finger in sorted(leap_hand.fingers, key=lambda f: f.type()):
            joints = list()
            self.joint_offsets.append(joints)
            for i in range(4):
                bone = finger.bone(i)
                if i == 0 and finger.type() != 0:
                    joints.append(Vec3(bone.prev_joint) - origin)
                joints.append(Vec3(bone.next_joint) - origin)

    def _json_dict(self):
        return {attr: getattr(self, attr) for attr in self.__slots__}

    def match_joint_offsets(self, other, threshold=45):
        for fa, fb in itertools.izip(self.joint_offsets, other.joint_offsets):
            for ja, jb in itertools.izip(fa, fb):
                if (ja - jb).length() > threshold:
                    return False
        return True