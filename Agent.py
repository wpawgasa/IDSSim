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

    def resetPlan(self):
        self.plan = {}



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
        self.pl = []
        self.status = 0 # 0 not operate, 1 patrolling, 2 investigating
        self.isFoundTrespasser = False
        self.investigating_time = 0
        self.found_trespasser = {}
        self.investigated_entity = None
        self.observing_confidence = np.random.random_sample()
        self.pomdp_active = False
        self.observation_history = {} # record all observations
        self.active_history = [] # record observation during POMDP
        self.belief = [] # initial belief of real observation
        self.T = {} # search tree
        self.explored_h = [] # explored history

    def getWTd(self):
        return self.w_td

    def getWOb(self):
        return self.w_ob

    def getWSt(self):
        return self.w_st

    def addPath(self, pa):
        self.pl.append(pa)

    def getPl(self):
        return self.pl

    def setPl(self, pl):
        self.pl = pl

    def setStatus(self, status):
        self.status = status

    def getStatus(self):
        return self.status

    def incrementInvestigatingTime(self):
        self.investigating_time = self.investigating_time + 1

    def resetInvestigatingTime(self):
        self.investigating_time = 0

    def getInvestigatingTime(self):
        return self.investigating_time

    def setInvestigatedEntity(self, e):
        self.investigated_entity = e

    def getInvestigatedEntity(self):
        return self.investigated_entity

    def addFoundTrespasser(self, period, stage, t):
        self.found_trespasser[(period, stage)] = t

    def resetFoundTrespasser(self):
        self.found_trespasser = {}

    def getObservingConfidence(self):
        return self.observing_confidence

    def getPOMDPStatus(self):
        return self.pomdp_active

    def setPOMDPStatus(self, status):
        self.pomdp_active = status

    def getObservationHistory(self):
        return self.observation_history

    def addObservation(self, stage, observer, fp):
        self.observation_history[(stage, observer)] = fp

    def getObservationHistory(self):
        return self.observation_history

    def resetObservation(self):
        self.observation_history = {}

    def getObservationAt(self, stage, observer):
        return self.observation_history[(stage, observer)]

    def addToBelief(self, b):
        self.belief.append(b)

    def getBelief(self):
        return self.belief

    def resetBelief(self):
        self.belief = []


class TrespasserAgent(Agent):
    def __init__(self, id, loc_en, loc_ex, arr_time, x, y, w, h, parent=None):
        super(TrespasserAgent, self).__init__(loc_en, x, y, w, h, parent)
        self.id = id
        self.isTarget = True
        self.setPen(QColor(237, 76, 62, 255))
        self.setBrush(QColor(237, 76, 62, 255))
        self.setToolTip(self.id)
        self.w_td = np.random.random_sample()
        self.w_ob = np.random.random_sample()
        self.w_st = np.random.random_sample()
        self.arr_time = arr_time
        self.entry_s = loc_en
        self.exit_s = loc_ex
        self.status = 0 # 0 not arrive yet, 1 in region, 2 detected, 3 exit region
        self.trespassed = []
        self.observing_confidence = np.random.random_sample()
        self.belief = []

    def getWTd(self):
        return self.w_td

    def getWOb(self):
        return self.w_ob

    def getWSt(self):
        return self.w_st

    def getArrTime(self):
        return self.arr_time

    def setStatus(self, status):
        self.status = status

    def getStatus(self):
        return self.status

    def addTrespassed(self, s):
        self.trespassed.append(s)

    def getTrespassed(self):
        return self.trespassed

    def getObservingConfidence(self):
        return self.observing_confidence

    def addToBelief(self, b):
        self.belief.append(b)

    def getBelief(self):
        return self.belief

    def resetBelief(self):
        self.belief = []

    def getDestination(self):
        return self.exit_s

class Noise(Agent):
    def __init__(self, id, loc, x, y, w, h, parent=None):
        super(Noise, self).__init__(loc, x, y, w, h, parent)
        self.id = id
        self.setPen(QColor(240, 130, 41, 255))
        self.setBrush(QColor(240, 130, 41, 255))
        self.arr_time = 0
        self.isTarget = False
    

    