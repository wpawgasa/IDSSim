class ObservedFootprint:

    def __init__(self, t, loc, value, confidence):
        self.t = t
        self.loc = loc
        self.value = value
        self.confidence = confidence
        self.Lambda = []
        self.b = {}