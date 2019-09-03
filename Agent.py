import sys
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class Agent(QGraphicsEllipseItem):
    def __init__(self, loc, x, y, w, h, parent=None):
        super(Agent, self).__init__(x, y, w, h, parent)
        self.initLoc = loc
        self.curLoc = loc
        self.plan = {}

    def setCurLoc(self, loc):
        self.curLoc = loc

    def getCurLoc(self):
        return self.curLoc

    def setInitLoc(self, loc):
        self.initLoc = loc

    def getInitLoc(self):
        return self.initLoc

    def addToPlan(self, key, segment):
        self.plan[key] = segment

    def getSegmentFromPlan(self, key):
        return self.plan[key]



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
    def __init__(self, id, loc_en, loc_ex, arr_time, x, y, w, h, parent=None):
        super(TrespasserAgent, self).__init__(loc_en, x, y, w, h, parent)
        self.id = id
        self.setPen(QColor(237, 76, 62, 255))
        self.setBrush(QColor(237, 76, 62, 255))
        self.setToolTip(self.id)
        self.w_td = np.random.random_sample()
        self.w_ob = np.random.random_sample()
        self.w_st = np.random.random_sample()
        self.arr_time = arr_time
        self.entry_s = loc_en
        self.exit_s = loc_ex

    def getWTd(self):
        return self.w_td

    def getWOb(self):
        return self.w_ob

    def getWSt(self):
        return self.w_st

    def getArrTime(self):
        return self.arr_time

class Noise(Agent):
    def __init__(self, id, loc, x, y, w, h, parent=None):
        super(Noise, self).__init__(loc, x, y, w, h, parent)
        self.id = id
        self.setPen(QColor(240, 130, 41, 255))
        self.setBrush(QColor(240, 130, 41, 255))
        self.arr_time = 0
    

    