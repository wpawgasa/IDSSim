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
        # self.de = 0
        self.L = 0
        # self.negative_m = 0
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

    # def getDe(self):
    #     return self.de
    #
    # def setDe(self, de):
    #     self.de = de

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
        
    def calScore(self, num_tres):
        if self.td == 1:
            self.L = 0
        elif num_tres > 0:
            self.L = (1-self.td)+self.ob+self.st/num_tres
        else:
            self.L = (1 - self.td) + self.ob

    def setL(self,L):
        self.L = L

    def getL(self):
        return self.L

    def setEntry(self, b):
        self.isEntry = b

    def getEntry(self):
        return self.isEntry

    def setExit(self, b):
        self.isExit = b

    def getExit(self):
        return self.isExit
