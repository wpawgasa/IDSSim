import sys
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class Agent(QGraphicsEllipseItem):
    def __init__(self, loc, x, y, w, h, parent=None):
        super(Agent, self).__init__(x, y, w, h, parent)
        self.curLoc = loc
        self.plan = []

    def setCurLoc(self,loc):
        self.curLoc = loc

    def getCurLoc(self):
        return self.curLoc



class PatrolAgent(Agent):
    def __init__(self, id, loc, x, y, w, h, parent=None):
        super(PatrolAgent, self).__init__(loc, x, y, w, h, parent)
        self.id = id
        self.setPen(QColor(0, 153, 255, 255))
        self.setBrush(QColor(0, 153, 255, 255))
        self.setToolTip(self.id)
        self.w_td = np.random.random_sample()
        self.w_ob = np.random.random_sample()
        self.w_st = np.random.random_sample()

class TrespasserAgent(Agent):
    def __init__(self, id, loc, x, y, w, h, parent=None):
        super(TrespasserAgent, self).__init__(loc, x, y, w, h, parent)
        self.id = id
        self.setPen(QColor(237, 76, 62, 255))
        self.setBrush(QColor(237, 76, 62, 255))
        self.setToolTip(self.id)
        self.w_td = np.random.random_sample()
        self.w_ob = np.random.random_sample()
        self.w_st = np.random.random_sample()

class Noise(Agent):
    def __init__(self, id, loc, x, y, w, h, parent=None):
        super(Noise, self).__init__(loc, x, y, w, h, parent)
        self.id = id
        self.setPen(QColor(240, 130, 41, 255))
        self.setBrush(QColor(240, 130, 41, 255))
    

    