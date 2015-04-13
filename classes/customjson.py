from json import JSONEncoder

class JSONEncoderPlus(JSONEncoder):
    def default(self, o):
        try:
            return o._custom_json()
        except AttributeError:
            return super(JSONEncoderPlus, self).default(self, o)