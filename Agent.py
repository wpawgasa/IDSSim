import sys
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class Agent(QGraphicsEllipseItem):
    def __init__(self, type, loc, x, y, w, h, parent=None):
        super(Agent, self).__init__(x, y, w, h, parent)
        self.type = type
        self.curLoc = loc
        self.sensor = None
        self.plan = {"path":[]}

    

    