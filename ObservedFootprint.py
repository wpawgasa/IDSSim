class ObservedFootprint:

    def __init__(self, source, origin, value, uncertainty, observed_t):
        self.source = source
        self.origin = origin
        self.value = value
        # uncertainty when construct a belief
        # depended on source's confidence and value
        # measure deviation from computed belief
        self.uncertainty = uncertainty
        self.observed_t = observed_t
