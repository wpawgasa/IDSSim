from PyQt5.QtWidgets import *
class FootprintSensor(QGraphicsEllipseItem):
    def __init__(self, loc, type, host, x, y, w, h, parent=None):
        super(FootprintSensor, self).__init__(x, y, w, h, parent)
        self.curLoc = loc
        # source type
        # - 0 equipped on host
        # - 1 remote sensor
        self.type = type
        # a border patrol who can directly observe from this sensor
        self.host = host
        # confidence of the source measure probability that it will retrieve fp value correctly
        # sensor coefficient
        # confidence is computed from sensor coef and obscurity in segment
        # range of fp value that can be sensed
