import sys
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class GridCell(QGraphicsRectItem):
    
    def __init__(self, x, y, w, h, parent=None):
        super(GridCell, self).__init__(x, y, w, h, parent)
        self._id = ""
        self.row = 0
        self.col = 0
        self.td = 0
        self.ob = 0
        self.st = 0
        self.de = 0
        self.positive_m = 0
        self.negative_m = 0
        self.isEntry = False
        self.isExit = False
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.scene().cellEntered.emit(self)
    
    def hoverLeaveEvent(self, event):
        self.scene().cellLeave.emit(self)

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getRow(self):
        return self.row

    def setRow(self, row):
        self.row = row

    def getCol(self):
        return self.col

    def setCol(self, col):
        self.col = col

    def getTd(self):
        return self.td

    def setTd(self, td):
        self.td = td

    def getOb(self):
        return self.ob

    def setOb(self, ob):
        self.ob = ob

    def getSt(self):
        return self.st

    def setSt(self, st):
        self.st = st

    def getDe(self):
        return self.de

    def setDe(self, de):
        self.de = de

    def isEntryCell(self):
        return self.isEntry

    def toggleEntryCell(self):
        if self.isEntry:
            self.isEntry = False
        else:
            self.isEntry = True

    def isExitCell(self):
        return self.isExit

    def toggleExitCell(self):
        if self.isExit:
            self.isExit = False
        else:
            self.isExit = True
        
    def calPositiveM(self, w_td, w_ob, w_st, w_de, sum_st):
        if self.td==1:
            self.positive_m = 0
        elif sum_st>0:
            # self.m = w_td*(1-self.td)+w_ob*self.ob+w_st*self.st/sum_st+w_de*(np.exp(-1*self.de))
            self.positive_m = w_td*(1-self.td)+w_ob*self.ob+w_st*self.st/sum_st+w_de*(1-self.de)
        else:
            self.positive_m = w_td*(1-self.td)+w_ob*self.ob+w_de*(1-self.de)

    def setPositiveM(self,m):
        self.positive_m = m

    def getPositiveM(self):
        return self.positive_m

    def calNegativeM(self, w_td, w_de):
        if self.td==1:
            self.negative_m = 0
        else:
            self.negative_m = w_td*(1-self.td)+w_de*(self.de)

    def getOffset(self):
        return self.positive_m - self.negative_m

    def setNegativeM(self,m):
        self.negative_m = m

    def getNegativeM(self):
        return self.negative_m

    def setEntry(self, b):
        self.isEntry = b

    def getEntry(self):
        return self.isEntry

    def setExit(self, b):
        self.isExit = b

    def getExit(self):
        return self.isExit