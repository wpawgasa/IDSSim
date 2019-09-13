import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from GridCell import *
import numpy as np

class Path(QPainterPath):

    def __init__(self):
        super().__init__()
        # self.p = p
        self.length = 0
        # self.agg_m = 0
        # self.duration = 0
        self.cells = []
        # self._id = 0
        # self.pathItem = None

    # def setId(self, id):
    #     self._id = id

    # def getId(self):
    #     return self._id

    # def aggregateM(self, w_td, w_ob, w_st):
    #     cell_td = [c.getTd() for c in self.cells]
    #     mean_td = np.mean(cell_td)
    #     cell_ob = [c.getOb() for c in self.cells]
    #     mean_ob = np.mean(cell_ob)
    #     cell_st = [c.getSt() for c in self.cells]
    #     mean_st = np.mean(cell_st)
    #     self.agg_m = w_td*(1-mean_td) + w_st*(mean_ob) + w_st*(mean_st)

    def addCell(self, cell):
        self.cells.append(cell)
        self.length = self.length + 1
        # self.agg_m = self.agg_m +
        # self.duration = self.duration + np.ceil(1/(1-cell.getTd()))
        return

    def removeCell(self, cell):
        self.cells.remove(cell)
        self.length = self.length - 1
        # self.agg_m = self.agg_m - (cell.getPositiveM()-cell.getNegativeM())
        # self.duration = self.duration - np.ceil(1/(1-cell.getTd()))
        return

    def getEndPoint(self):
        return self.cells[-1]

    # def containCell(self, cell):
    #     return super.contains(cell.rect.center)

    def getLength(self):
        return self.length

    def getCells(self):
        return self.cells

    # def getAggM(self):
    #     return self.agg_m

    # def setPathItem(self, item):
    #     self.pathItem = item

    # def getPathItem(self):
    #     return self.pathItem



class PatrolPath(Path):

    def __init__(self, p):
        super(PatrolPath, self).__init__()
        self.p = p
        self.agg_m = 0

    def addPatrolCell(self, cell, m):
        self.addCell(cell)
        self.agg_m = self.agg_m + m

    def removePatrolCell(self, cell, m):
        self.removeCell(cell)
        self.agg_m = self.agg_m - m

    def getRepeatGaurdSegments(self, guard):
        if guard > len(self.cells):
            return self.cells
        else:
            return self.cells[-guard]

    def getAggM(self):
        return self.agg_m


