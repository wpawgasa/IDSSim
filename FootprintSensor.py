from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import numpy as np

class FootprintSensor(QGraphicsEllipseItem):
    def __init__(self, loc, host, x, y, w, h, parent=None):
        super(FootprintSensor, self).__init__(x, y, w, h, parent)
        self.setPen(QColor(105, 245, 120, 255))
        self.setBrush(QColor(105, 245, 120, 255))
        self.curLoc = loc
        # a border patrol who can directly observe from this sensor
        self.host = host
        self.lastDetectedFP = None
        self.curDetectedFP = None


    def setLoc(self, loc):
        self.curLoc = loc
