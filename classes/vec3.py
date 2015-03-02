import math

class Vec3(object):

    __slots__ = "x y z".split()

    def __init__(self, *args):
        if len(args) == 0:
            self.x = 0
            self.y = 0
            self.z = 0
        elif len(args) == 1:
            other = args[0]
            if type(other) == dict:
                self.x = float(other['x'])
                self.y = float(other['y'])
                self.z = float(other['z'])
            else:
                self.x = other.x
                self.y = other.y
                self.z = other.z
        elif len(args) == 3:
            self.x, self.y, self.z = args
        else:
            raise TypeError(
                "Vec3 given %d args; expected 0, 1, or 3" % len(args)
            )

    def length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def _json_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }

    def __repr__(self):
        return "Vec3(%s, %s, %s)" % (self.x, self.y, self.z)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __eq__(self, other):
        return self.x == other.x and \
            self.y == other.y and \
            self.z == other.z

    def __ne__(self, other):
        return not (self == other)

    def __neg__(self):
        return Vec3(
            -self.x,
            -self.y,
            -self.z,
        )

    def __add__(self, other):
        return Vec3(
            self.x+other.x,
            self.y+other.y,
            self.z+other.z,
        )

    def __sub__(self, other):
        return self + (-other)