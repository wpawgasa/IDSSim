import sys
import numpy as np
import scipy.special as sp
import operator
import csv
import sip
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from GridCell import *
from Path import *
from functools import partial
sip.setapi('QString',2)
sip.setapi('QVariant',2)

class SimScene(QGraphicsScene):
    cellEntered = pyqtSignal([QGraphicsItem],[QGraphicsWidget])
    cellLeave = pyqtSignal([QGraphicsItem],[QGraphicsWidget])

class BorderSim(QWidget):
    def __init__(self):
        super().__init__()

        self.number_row = 0
        self.number_col = 0

        self.patrollers = {"agents":[]}
        self.intruders = {"agents":[]}
        self.others = {"agents":[]}
        self.segments = {"segments":[]}

        self.w_td = 1.0
        self.w_ob = 1.0
        self.w_st = 1.0
        self.w_de = 1.0
        self.w_td_n = 1.0
        self.w_de_n = 1.0
        self.sum_st = 0
        self.intruder_arr_model = 1
        self.intruder_mov_model = 1
        self.intruder_arr_rate = 0
        self.other_arr_model = 1
        self.other_arr_rate = 0
        self.patroller_mov_model = 1
        self.num_patroller = 0

        self.entry_prob = []
        self.totalStat = 0
        self.targetlifetime = 0.5 #target is active after time period

        self.number_i_entry = 0    #number of intruder entering the area during the period
        self.number_o_entry = 0    #number of regular trespasser entering the area during the period
        self.number_i_exit = 0   #number of intruder exiting the area through the exit line
        self.number_o_exit = 0
        self.number_i_detected = 0 #number of intruder detected by a sensors (true detection)
        self.number_o_detected = 0 #number of intruder detected by a sensors (false detection)

        self.num_period = 1
        self.period_len = 100
        self.stage_duration = 0.1

        layout = QHBoxLayout()      
        self.setSimScene()
        tabView = self.createTabView()
        layout.addWidget(self.view)
        layout.addWidget(tabView)
        self.setLayout(layout)
        self.setFixedSize(1400,800)
        self.show()

    def setSimScene(self):
        self.font = QFont("Consolas")
        self.font.setPointSize(10)
        self.font.setWeight(25)

        self.redpalette = QPalette()
        self.redpalette.setColor(QPalette.Text, Qt.red)
        self.yellowpalette = QPalette()
        self.yellowpalette.setColor(QPalette.Text, Qt.yellow)
        self.bluepalette = QPalette()
        self.bluepalette.setColor(QPalette.Text, Qt.blue)
        self.greenpalette = QPalette()
        self.greenpalette.setColor(QPalette.Text, Qt.green)
        self.pinkpalette = QPalette()
        self.pinkpalette.setColor(QPalette.Text, QColor(255, 0, 102, 255))
        self.purplepalette = QPalette()
        self.purplepalette.setColor(QPalette.Text, QColor(153, 0, 255, 255))

        self.scene = SimScene(self)
        self.scene.setBackgroundBrush(QColor(0,0,0,255))
        self.scene.cellEntered.connect(self.handleCellEntered)
        self.scene.cellLeave.connect(self.handleCellLeave)

        self.display_row = self.scene.addText("Row: ")
        self.display_row.setPos(10,5)
        self.display_row.setFont(self.font)
        self.display_col = self.scene.addText("Column: ")
        self.display_col.setPos(50,5)
        self.display_col.setFont(self.font)
        self.display_td = self.scene.addText("Difficulty: ")
        self.display_td.setPos(110,5)
        self.display_td.setFont(self.font)
        self.display_ob = self.scene.addText("Obscurity: ")
        self.display_ob.setPos(200,5)
        self.display_ob.setFont(self.font)
        self.display_st = self.scene.addText("Statistic: ")
        self.display_st.setPos(280,5)
        self.display_st.setFont(self.font)
        self.display_m = self.scene.addText("Offset: ")
        self.display_m.setPos(10,15)
        self.display_m.setFont(self.font)

        self.display_row_val = self.scene.addText("-")
        self.display_row_val.setPos(35,5)
        self.display_row_val.setFont(self.font)
        self.display_row_val.setDefaultTextColor(QColor(255, 255, 0, 255))
        self.display_col_val = self.scene.addText("-")
        self.display_col_val.setPos(90,5)
        self.display_col_val.setFont(self.font)
        self.display_col_val.setDefaultTextColor(QColor(255, 255, 0, 255))
        self.display_td_val = self.scene.addText("-")
        self.display_td_val.setPos(173,5)
        self.display_td_val.setFont(self.font)
        self.display_td_val.setDefaultTextColor(QColor(255, 0, 0, 255))
        self.display_ob_val = self.scene.addText("-")
        self.display_ob_val.setPos(258,5)
        self.display_ob_val.setFont(self.font)
        self.display_ob_val.setDefaultTextColor(QColor(153, 0, 255, 255))
        self.display_st_val = self.scene.addText("-")
        self.display_st_val.setPos(340,5)
        self.display_st_val.setFont(self.font)
        self.display_st_val.setDefaultTextColor(QColor(255, 0, 102, 255))
        self.display_m_val = self.scene.addText("-")
        self.display_m_val.setPos(80,15)
        self.display_m_val.setFont(self.font)
        self.display_m_val.setDefaultTextColor(QColor(0, 0, 255, 255))
        

        self.view = QGraphicsView(self)
        self.view.setFixedSize(500,800)
        self.view.setSceneRect(0,0,500,800)
        
        self.view.fitInView(0,0,500,800,Qt.KeepAspectRatio)
        
        self.view.setScene(self.scene)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    def handleCellEntered(self, cell):
        # print(cell.getId())
        self.display_row_val.setPlainText(str(cell.getRow()))
        self.display_col_val.setPlainText(str(cell.getCol()))
        self.display_td_val.setPlainText(str(cell.getTd()))
        self.display_ob_val.setPlainText(str(cell.getOb()))
        self.display_st_val.setPlainText(str(cell.getSt()))
        self.display_m_val.setPlainText(str(cell.getOffset()))
    
    def handleCellLeave(self, cell):
        # print(cell.getId())
        self.display_row_val.setPlainText("-")
        self.display_col_val.setPlainText("-")
        self.display_td_val.setPlainText("-")
        self.display_ob_val.setPlainText("-")
        self.display_st_val.setPlainText("-")
        self.display_m_val.setPlainText("-")

    def createTabView(self):
        tabView = QTabWidget()
        envSettingTab = QWidget()
        agentSettingTab = QWidget()
        simCtrlTab = QWidget()
        resultTab = QWidget()
        
        tabView.addTab(envSettingTab,"Environment")
        tabView.addTab(agentSettingTab,"Agents")
        tabView.addTab(simCtrlTab,"Simulation")
        tabView.addTab(resultTab,"Result")
        envLayOut = self.createEnvSettingLayOut()
        envSettingTab.setLayout(envLayOut)
        agentLayOut = self.createAgentSettingLayOut()
        agentSettingTab.setLayout(agentLayOut)
        simLayOut = self.createSimCtrlLayOut()
        simCtrlTab.setLayout(simLayOut)
        return tabView
        

    def createEnvSettingLayOut(self):
        layout = QFormLayout()
        dimension = QHBoxLayout()
        dimensionW = QSpinBox()
        dimensionW.setRange(0,500)
        dimensionW.valueChanged.connect(self.onColChanged)
        dimensionH = QSpinBox()
        dimensionH.setRange(0,1000)
        dimensionH.valueChanged.connect(self.onRowChanged)
        WLabel = QLabel("Columns (Width)")
        HLabel = QLabel("Rows (Height)")
        dimension.addWidget(WLabel)
        dimension.addWidget(dimensionW)
        dimension.addWidget(HLabel)
        dimension.addWidget(dimensionH)
        layout.addRow("Region Dimension:",dimension)
        buttonLayOut = QHBoxLayout()
        setbutton = QPushButton("Draw Region")
        setbutton.clicked.connect(self.drawGrid)
        loadTDbutton = QPushButton("Load TD")
        loadTDbutton.clicked.connect(self.openTDFileDialog)
        loadOBbutton = QPushButton("Load OB")
        loadOBbutton.clicked.connect(self.openOBFileDialog)
        loadSTbutton = QPushButton("Load ST")
        loadSTbutton.clicked.connect(self.openSTFileDialog)
        buttonLayOut.addWidget(setbutton)
        buttonLayOut.addWidget(loadTDbutton)
        buttonLayOut.addWidget(loadOBbutton)
        buttonLayOut.addWidget(loadSTbutton)
        layout.addRow(buttonLayOut)

        posweightLayout = QHBoxLayout()
        posweightTDLabel = QLabel("+TD weight")
        posweightOBLabel = QLabel("+OB weight")
        posweightSTLabel = QLabel("+ST weight")
        posweightDELabel = QLabel("+DE weight")
        posweightTD = QDoubleSpinBox()
        posweightTD.setRange(0.0,1.0)
        posweightTD.setValue(1.0)
        posweightTD.valueChanged.connect(self.onPosTDChanged)
        posweightOB = QDoubleSpinBox()
        posweightOB.setRange(0.0,1.0)
        posweightOB.setValue(1.0)
        posweightOB.valueChanged.connect(self.onPosOBChanged)
        posweightST = QDoubleSpinBox()
        posweightST.setRange(0.0,1.0)
        posweightST.setValue(1.0)
        posweightST.valueChanged.connect(self.onPosSTChanged)
        posweightDE = QDoubleSpinBox()
        posweightDE.setRange(0.0,1.0)
        posweightDE.setValue(1.0)
        posweightDE.valueChanged.connect(self.onPosDEChanged)
        posweightLayout.addWidget(posweightTDLabel)
        posweightLayout.addWidget(posweightTD)
        posweightLayout.addWidget(posweightOBLabel)
        posweightLayout.addWidget(posweightOB)
        posweightLayout.addWidget(posweightSTLabel)
        posweightLayout.addWidget(posweightST)
        posweightLayout.addWidget(posweightDELabel)
        posweightLayout.addWidget(posweightDE)
        layout.addRow(posweightLayout)

        negweightLayout = QHBoxLayout()
        negweightTDLabel = QLabel("-TD weight")
        negweightDELabel = QLabel("-DE weight")
        negweightTD = QDoubleSpinBox()
        negweightTD.setRange(0.0,1.0)
        negweightTD.setValue(1.0)
        negweightTD.valueChanged.connect(self.onNegTDChanged)
        negweightDE = QDoubleSpinBox()
        negweightDE.setRange(0.0,1.0)
        negweightDE.setValue(1.0)
        negweightDE.valueChanged.connect(self.onNegDEChanged)
        negweightLayout.addWidget(negweightTDLabel)
        negweightLayout.addWidget(negweightTD)
        negweightLayout.addWidget(negweightDELabel)
        negweightLayout.addWidget(negweightDE)
        layout.addRow(negweightLayout)

        box2Layout = QHBoxLayout()

        areaViewLayout = QHBoxLayout()
        areaViewLabel = QLabel("View Selection")
        viewSelNone = QRadioButton("None")
        viewSelNone.setChecked(True)
        viewSelTD = QRadioButton("Difficulty")
        viewSelOB = QRadioButton("Obscurity")
        viewSelST = QRadioButton("Statistic")
        viewSelNone.toggled.connect(self.changeToNoneView)
        viewSelTD.toggled.connect(self.changeToTDView)
        areaViewLayout.addWidget(areaViewLabel)
        areaViewLayout.addWidget(viewSelNone)
        areaViewLayout.addWidget(viewSelTD)
        areaViewLayout.addWidget(viewSelOB)
        areaViewLayout.addWidget(viewSelST)
        areaViewLayout.setAlignment(Qt.AlignLeft)
        
        box2Layout.addLayout(areaViewLayout)

        layout.addRow(box2Layout)

        box3Layout = QHBoxLayout()

        pathViewLayout = QVBoxLayout()
        
        calPathBtn = QPushButton("Determine Possible Crossing Paths")
        # viewPath = QCheckBox("Show Paths")
        # viewPath.setChecked(True)
        calPathBtn.clicked.connect(self.calPaths)
        pathViewLayout.addWidget(calPathBtn)
        # pathViewLayout.addWidget(viewPath)
        self.pathTbl = QTableWidget(0,4)
        header_labels = ['Path', 'Length', 'Duration', 'Significance']
        self.pathTbl.setHorizontalHeaderLabels(header_labels)
        self.pathTbl.setFixedSize(500,300)
        self.pathTbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.pathTbl.setSelectionMode(QAbstractItemView.MultiSelection)
        self.pathTbl.setStyleSheet("QTableWidget::item:selected{ background-color: red }")
        self.pathTbl.itemSelectionChanged.connect(self.drawPath)
        # self.pathTbl.setSortingEnabled(True)
        
        pathViewLayout.addWidget(self.pathTbl)

        otherpathViewLayout = QVBoxLayout()
        
        calOtherPathBtn = QPushButton("Determine Possible Non-crossing Paths")
        # viewPath = QCheckBox("Show Paths")
        # viewPath.setChecked(True)
        calOtherPathBtn.clicked.connect(self.calOtherPaths)
        otherpathViewLayout.addWidget(calOtherPathBtn)
        # pathViewLayout.addWidget(viewPath)
        self.otherpathTbl = QTableWidget(0,4)
        # header_labels = ['Path', 'Length', 'Duration', 'Significance']
        self.otherpathTbl.setHorizontalHeaderLabels(header_labels)
        self.otherpathTbl.setFixedSize(500,300)
        self.otherpathTbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.otherpathTbl.setSelectionMode(QAbstractItemView.MultiSelection)
        self.otherpathTbl.setStyleSheet("QTableWidget::item:selected{ background-color: yellow }")
        self.otherpathTbl.itemSelectionChanged.connect(self.drawOtherPath)
        # self.pathTbl.setSortingEnabled(True)
        
        otherpathViewLayout.addWidget(self.otherpathTbl)

        box3Layout.addLayout(pathViewLayout)
        box3Layout.addLayout(otherpathViewLayout)

        layout.addRow(box3Layout)

        return layout

    def createAgentSettingLayOut(self):
        layout = QFormLayout()
        trespasserLayout = QHBoxLayout()
        patrollerLayout = QHBoxLayout()
        
        intruderGroupBox = QGroupBox("Intruder Agent")
        intruderLayout = QFormLayout()
        intruderArrModel = QHBoxLayout()
        poissonArr = QRadioButton("Poisson")
        paretoArr = QRadioButton("Pareto")
        poissonArr.setChecked(True)
        intruderArrModel.addWidget(poissonArr)
        intruderArrModel.addWidget(paretoArr)
        intruderLayout.addRow("Arrival Model: ", intruderArrModel)

        intruderArrRate = QSpinBox()
        intruderArrRate.setRange(0,100)
        intruderArrRate.setSingleStep(1)
        intruderArrRate.setValue(0)
        intruderLayout.addRow("Arrival Rate: ", intruderArrRate)
        intruderGroupBox.setLayout(intruderLayout)

        intruderMovementModel = QVBoxLayout()
        intruderRandomMove = QRadioButton("Random Movement")
        intruderRandomPossible = QRadioButton("Random Paths")
        intruderShortestPath = QRadioButton("Shortest Paths")
        intruderFastestPath = QRadioButton("Fastest Paths")
        intruderObscurePath = QRadioButton("Most Obscured Paths")
        poissonArr.setChecked(True)
        intruderArrModel.addWidget(poissonArr)
        intruderArrModel.addWidget(paretoArr)
        intruderLayout.addRow("Arrival Model: ", intruderArrModel)

        otherGroupBox = QGroupBox("Other Trespasser Agent")
        otherLayout = QFormLayout()
        otherArrModel = QHBoxLayout()
        poissonArrOther = QRadioButton("Poisson")
        paretoArrOther = QRadioButton("Pareto")
        poissonArrOther.setChecked(True)
        otherArrModel.addWidget(poissonArrOther)
        otherArrModel.addWidget(paretoArrOther)
        otherLayout.addRow("Arrival Model: ", otherArrModel)

        otherArrRate = QSpinBox()
        otherArrRate.setRange(0,100)
        otherArrRate.setSingleStep(1)
        otherArrRate.setValue(0)
        otherLayout.addRow("Arrival Rate: ", otherArrRate)
        otherGroupBox.setLayout(otherLayout)

        trespasserLayout.addWidget(intruderGroupBox)
        trespasserLayout.addWidget(otherGroupBox)

        patrollerGroupBox = QGroupBox("Patroller Agent")
        patrollerLayout = QFormLayout()
        patrollerNumber = QSpinBox()
        patrollerNumber.setRange(0,100)
        patrollerNumber.setSingleStep(1)
        patrollerNumber.setValue(1)
        patrollerLayout.addRow("Number of patrollers: ", patrollerNumber)
        placePatroller = QPushButton("Place Patrollers")
        patrollerLayout.addRow(placePatroller)

        patrollerMovementModel = QHBoxLayout()
        heuristicModel = QRadioButton("Conformant Plan (Heuristic)")
        pomdpModel = QRadioButton("Online Plan (POMDP)")
        heuristicModel.setChecked(True)
        patrollerMovementModel.addWidget(heuristicModel)
        patrollerMovementModel.addWidget(pomdpModel)
        patrollerLayout.addRow("Movement Model: ", patrollerMovementModel)
        patrollerGroupBox.setLayout(patrollerLayout)

        layout.addRow(trespasserLayout)
        layout.addRow(patrollerLayout)
        return layout

    def createSimCtrlLayOut(self):
        layout = QFormLayout()
        numPeriod = QSpinBox()
        numPeriod.setRange(0,100)
        numPeriod.setSingleStep(1)
        numPeriod.setValue(1)
        numPeriod.valueChanged.connect(self.onNumPeriodChanged)
        layout.addRow("Number of Periods", numPeriod)
        operPeriod = QSpinBox()
        operPeriod.setRange(0,5000)
        operPeriod.setSingleStep(10)
        operPeriod.setValue(100)
        operPeriod.valueChanged.connect(self.onPeriodLengthChanged)
        layout.addRow("Period length", operPeriod)
        stageDuration = QDoubleSpinBox()
        stageDuration.setRange(0,1)
        stageDuration.setSingleStep(0.01)
        stageDuration.setValue(0.1)
        stageDuration.valueChanged.connect(self.onStageDurationChanged)
        layout.addRow("Stage Duration", stageDuration)

        simcontrolBtn = QHBoxLayout()
        runButton = QPushButton("Run Simulation")
        runButton.clicked.connect(self.startSim)
        pauseButton = QPushButton("Pause Simulation")
        pauseButton.clicked.connect(self.pauseSim)
        resetButton = QPushButton("Reset Simulation")
        resetButton.clicked.connect(self.resetSim)
        simcontrolBtn.addWidget(runButton)
        simcontrolBtn.addWidget(pauseButton)
        simcontrolBtn.addWidget(resetButton)
        layout.addRow(simcontrolBtn)

        simStatusGroupBox = QGroupBox("Simulation Status")
        simStatusLayout = QHBoxLayout()
        simCurrentPeriodLabel = QLabel("Current Period")
        simCurrentPeriod = QLabel(str(0))
        simCurrentStageLabel = QLabel("Current Stage")
        simCurrentStage = QLabel(str(0))
        simStatusLayout.addWidget(simCurrentPeriodLabel)
        simStatusLayout.addWidget(simCurrentPeriod)
        simStatusLayout.addWidget(simCurrentStageLabel)
        simStatusLayout.addWidget(simCurrentStage)
        simStatusGroupBox.setLayout(simStatusLayout)

        layout.addRow(simStatusGroupBox)

        return layout

    def createResultLayOut(self):
        layout = QFormLayout()
        return layout

    def onRowChanged(self, value):
        self.number_row = value

    def onColChanged(self, value):
        self.number_col = value

    def onPosTDChanged(self, value):
        self.w_td = value

    def onPosOBChanged(self, value):
        self.w_ob = value

    def onPosSTChanged(self, value):
        self.w_st = value

    def onPosDEChanged(self, value):
        self.w_de = value

    def onNegTDChanged(self, value):
        self.w_td_n = value

    def onNegDEChanged(self, value):
        self.w_de_n = value

    def onNumPeriodChanged(self, value):
        self.num_period = value

    def onPeriodLengthChanged(self, value):
        self.period_len = value

    def onStageDurationChanged(self, value):
        self.stage_duration = value

    def drawGrid(self):
        self.pos_x = 10
        self.pos_y = 35
        self.grid_width = 10
        for s in self.segments["segments"]:
            self.scene.removeItem(s["obj"])
            
        self.segments = {"segments":[]}
        while self.grid_width*self.number_col > 480:
            self.grid_width = self.grid_width*0.95

        for j in range(0,self.number_row):
            
            for i in range(0,self.number_col):

                segment = GridCell(self.pos_x+i*self.grid_width,self.pos_y+j*self.grid_width,
                    self.grid_width,self.grid_width)
                
                segment.setPen(QColor(Qt.white))
                segment.setBrush(QBrush(Qt.NoBrush))

                self.scene.addItem(segment)
                
                # segment = GridCell(j+1,i+1,rect)
                segment.setRow(j+1)
                segment.setCol(i+1)
                segment.setId("Cell_"+str(j+1)+"_"+str(i+1))
                segment.setDe((self.number_col-(i+1))/(self.number_col-1))
                if i == 0:
                    segment.setEntry(True)
                elif i == self.number_col-1:
                    segment.setExit(True)
                segment.calPositiveM(self.w_td, self.w_ob, self.w_st, self.w_de, self.sum_st)
                segment.calNegativeM(self.w_td_n, self.w_de_n)
                
                # rect.setToolTip("td: %f ob: %f st: %f de: %f m: %f" % 
                #     (segment.getTd(),segment.getOb(),segment.getSt(),segment.getDe(),segment.getM()))
                
                self.segments["segments"].append({"row":j+1, "col":i+1, "key":segment.getId(),"obj":segment})

        
        self.view.setScene(self.scene)

    def sumSt(self):
        return sum(x["obj"].getSt() for x in self.segments["segments"])

    def openTDFileDialog(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setNameFilter("CSV (*.csv)")
	
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            f = open(filenames[0], "r")
			
            with f:
                i_col = 1
                i_row = 1
                d = 0
                
                for row in csv.reader(f):
                    if i_row<=self.number_row:
                        for field in row:
                            if i_col<=self.number_col:
                                s = self.segments["segments"][d]["obj"]
                                # print("%i %i" % (i_row,i_col))
                                s.setTd(float(field))
                                s.calPositiveM(self.w_td, self.w_ob, self.w_st, self.w_de, self.sum_st)
                                s.calNegativeM(self.w_td_n, self.w_de_n)
                
                                d = d+1
                                i_col = i_col+1
                        i_row = i_row+1
                        i_col = 1

    def openOBFileDialog(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setNameFilter("CSV (*.csv)")
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            f = open(filenames[0], "r")
			
            with f:
                i_col = 1
                i_row = 1
                d = 0
                for row in csv.reader(f):
                    if i_row<=self.number_row:
                        for field in row:
                            if i_col<=self.number_col:
                                s = self.segments["segments"][d]["obj"]
                                s.setOb(float(field))
                                s.calPositiveM(self.w_td, self.w_ob, self.w_st, self.w_de, self.sum_st)
                                s.calNegativeM(self.w_td, self.w_td_n)
                                d = d+1
                                i_col = i_col+1
                        i_row = i_row+1
                        i_col = 1

    def openSTFileDialog(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setNameFilter("CSV (*.csv)")
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            f = open(filenames[0], "r")
			
            with f:
                i_col = 1
                i_row = 1
                d = 0
                for row in csv.reader(f):
                    if i_row<=self.number_row:
                        for field in row:
                            if i_col<=self.number_col:
                                s = self.segments["segments"][d]["obj"]
                                s.setSt(float(field))
                                self.sum_st = self.sumSt()
                                s.calPositiveM(self.w_td, self.w_ob, self.w_st, self.w_de, self.sum_st)
                                s.calNegativeM(self.w_td_n, self.w_de_n)
                                d = d+1
                                i_col = i_col+1
                        i_row = i_row+1
                        i_col = 1                        
                

    def changeToNoneView(self):
        # print('none')
        if self.segments == {"segments":[]}:
            # print('empty')
            return
    
        for d in self.segments["segments"]:
            segment = d["obj"]
            red = 0
            green = 0
            blue = 0
            alpha = 0
            segment.setBrush(QColor(red, green, blue, alpha))

    def changeToTDView(self):
        # print('td')
        if self.segments == {"segments":[]}:
            return
    
        for d in self.segments["segments"]:
            segment = d["obj"]
            red = 255
            green = 0
            blue = 0
            alpha = 255*segment.getTd()       
            segment.setBrush(QColor(red, green, blue, alpha))

    def calPaths(self):
        if self.segments == {"segments":[]}:
            return
        entries = []
        for d in self.segments["segments"]:
            segment = d["obj"]
            if segment.getTd() < 1 and segment.getEntry():
                entries.append(segment)

        # print(entries)
        incompleted_paths = []
        completed_paths = []
        for e in entries:
            path = []
            path.append(e)
            incompleted_paths.append(path)

        while len(incompleted_paths) > 0:

            path = incompleted_paths[-1]
            endpoint = path[-1]
            if endpoint.getExit():
                incompleted_paths.remove(path)
                completed_paths.append(path)

            else:

                tt = self.findSegment(endpoint.getRow()-1, endpoint.getCol())
                tr = self.findSegment(endpoint.getRow()-1, endpoint.getCol()+1)
                rr = self.findSegment(endpoint.getRow(), endpoint.getCol()+1)
                br = self.findSegment(endpoint.getRow()+1, endpoint.getCol()+1)
                bb = self.findSegment(endpoint.getRow()+1, endpoint.getCol())
                bl = self.findSegment(endpoint.getRow()+1, endpoint.getCol()-1)
                ll = self.findSegment(endpoint.getRow(), endpoint.getCol()-1)
                tl = self.findSegment(endpoint.getRow()-1, endpoint.getCol()-1)
                path_found = 0
                if (tt is not None) and (not self.findLoopInPath(path,tt)) and tt.getTd() < 1:
                    path_found = path_found+1
                    if path_found == 1:
                        path.append(tt)
                    else:
                        new_path = path[:-1]
                        new_path.append(tt)
                        incompleted_paths.append(new_path)

                if (tr is not None) and (not self.findLoopInPath(path,tr)) and tr.getTd() < 1:
                    path_found = path_found+1
                    if path_found == 1:
                        path.append(tr)
                    else:
                        new_path = path[:-1]
                        new_path.append(tr)
                        incompleted_paths.append(new_path)

                if (rr is not None) and (not self.findLoopInPath(path,rr)) and rr.getTd() < 1:
                    path_found = path_found+1
                    if path_found == 1:
                        path.append(rr)
                    else:
                        new_path = path[:-1]
                        new_path.append(rr)
                        incompleted_paths.append(new_path)
                if (br is not None) and (not self.findLoopInPath(path,br)) and br.getTd() < 1:
                    path_found = path_found+1
                    if path_found == 1:
                        path.append(br)
                    else:
                        new_path = path[:-1]
                        new_path.append(br)
                        incompleted_paths.append(new_path)
                if (bb is not None) and (not self.findLoopInPath(path,bb)) and bb.getTd() < 1:
                    path_found = path_found+1
                    if path_found == 1:
                        path.append(bb)
                    else:
                        new_path = path[:-1]
                        new_path.append(bb)
                        incompleted_paths.append(new_path)
                if (bl is not None) and (not self.findLoopInPath(path,bl)) and bl.getTd() < 1:
                    path_found = path_found+1
                    if path_found == 1:
                        path.append(bl)
                    else:
                        new_path = path[:-1]
                        new_path.append(bl)
                        incompleted_paths.append(new_path)
                if (ll is not None) and (not self.findLoopInPath(path,ll)) and ll.getTd() < 1:
                    path_found = path_found+1
                    if path_found == 1:
                        path.append(ll)
                    else:
                        new_path = path[:-1]
                        new_path.append(ll)
                        incompleted_paths.append(new_path)
                if (tl is not None) and (not self.findLoopInPath(path,tl)) and tl.getTd() < 1:
                    path_found = path_found+1
                    if path_found == 1:
                        path.append(tl)
                    else:
                        new_path = path[:-1]
                        new_path.append(tl)
                        incompleted_paths.append(new_path)

                if path_found == 0:
                    incompleted_paths.remove(path)

        # print(incompleted_paths)
        print(len(completed_paths))
        path_cnt = 0
        self.pathTbl.clearContents()
        self.pathTbl.setSortingEnabled(False)

        for p in completed_paths:
            path = Path()
            path.setId(path_cnt+1)
            for s in p:
                if path.getLength() == 0:
                    path.moveTo(s.rect().center())
                else:
                    path.lineTo(s.rect().center())
                    path.moveTo(s.rect().center())
                path.addCell(s)
            # self.scene.addPath(path,QPen(QColor(0,153,255,255),1,Qt.SolidLine),QBrush(Qt.NoBrush))
            path.aggregateM(self.w_td,self.w_ob,self.w_st)
            # print(path.getAggM())
            self.pathTbl.insertRow(path_cnt)
            item0 = QTableWidgetItem()
            item0.setData(Qt.DisplayRole, path.getId())
            item1 = QTableWidgetItem()
            item1.setData(Qt.DisplayRole, path.getLength())
            item2 = QTableWidgetItem()
            item2.setData(Qt.DisplayRole, float(path.getDuration()))
            item3 = QTableWidgetItem()
            item3.setData(Qt.DisplayRole, float(path.getAggM()))
            self.pathTbl.setItem(path_cnt,0, item0)
            self.pathTbl.setItem(path_cnt,1, item1)
            self.pathTbl.setItem(path_cnt,2, item2)
            self.pathTbl.setItem(path_cnt,3, item3)
            self.possible_paths["paths"].append(path)
            path_cnt = path_cnt + 1
        
        self.pathTbl.setSortingEnabled(True)
                

    def drawPath(self):
        for p in self.possible_paths["paths"]:
            item = p.getPathItem()
            if item is not None:
                self.scene.removeItem(item)
                p.setPathItem(None)

        for index in sorted(self.pathTbl.selectionModel().selectedRows()):
            row = index.row()
            id = int(self.pathTbl.item(row,0).text())
            path = [p for p in self.possible_paths["paths"] if p.getId()==id] 
            if len(path)>0:
                # self.scene.removeItem(path[0])
                pathItem = self.scene.addPath(path[0],QPen(QColor(255,0,0,255),1,Qt.SolidLine),QBrush(Qt.NoBrush))
                path[0].setPathItem(pathItem)

    def calOtherPaths(self):
        if self.segments == {"segments":[]}:
            return
        entries = []
        for d in self.segments["segments"]:
            segment = d["obj"]
            if segment.getTd() < 1 and segment.getEntry():
                entries.append(segment)

        # print(entries)
        incompleted_paths = []
        completed_paths = []
        for e in entries:
            path = []
            path.append(e)
            incompleted_paths.append(path)

        while len(incompleted_paths) > 0:

            path = incompleted_paths[-1]
            endpoint = path[-1]
            # if endpoint.getExit():
            #     incompleted_paths.remove(path)
            #     completed_paths.append(path)
            # else:

            tt = self.findSegment(endpoint.getRow()-1, endpoint.getCol())
            tr = self.findSegment(endpoint.getRow()-1, endpoint.getCol()+1)
            rr = self.findSegment(endpoint.getRow(), endpoint.getCol()+1)
            br = self.findSegment(endpoint.getRow()+1, endpoint.getCol()+1)
            bb = self.findSegment(endpoint.getRow()+1, endpoint.getCol())
            bl = self.findSegment(endpoint.getRow()+1, endpoint.getCol()-1)
            ll = self.findSegment(endpoint.getRow(), endpoint.getCol()-1)
            tl = self.findSegment(endpoint.getRow()-1, endpoint.getCol()-1)
            path_found = 0
            if (tt is not None) and (not self.findLoopInPath(path,tt)) and tt.getTd() < 1:
                path_found = path_found+1
                if path_found == 1:
                    path.append(tt)
                else:
                    new_path = path[:-1]
                    new_path.append(tt)
                    incompleted_paths.append(new_path)

            if (tr is not None) and (not self.findLoopInPath(path,tr)) and tr.getTd() < 1:
                path_found = path_found+1
                if path_found == 1:
                    path.append(tr)
                else:
                    new_path = path[:-1]
                    new_path.append(tr)
                    incompleted_paths.append(new_path)

            if (rr is not None) and (not self.findLoopInPath(path,rr)) and rr.getTd() < 1:
                path_found = path_found+1
                if path_found == 1:
                    path.append(rr)
                else:
                    new_path = path[:-1]
                    new_path.append(rr)
                    incompleted_paths.append(new_path)
            if (br is not None) and (not self.findLoopInPath(path,br)) and br.getTd() < 1:
                path_found = path_found+1
                if path_found == 1:
                    path.append(br)
                else:
                    new_path = path[:-1]
                    new_path.append(br)
                    incompleted_paths.append(new_path)
            if (bb is not None) and (not self.findLoopInPath(path,bb)) and bb.getTd() < 1:
                path_found = path_found+1
                if path_found == 1:
                    path.append(bb)
                else:
                    new_path = path[:-1]
                    new_path.append(bb)
                    incompleted_paths.append(new_path)
            if (bl is not None) and (not self.findLoopInPath(path,bl)) and bl.getTd() < 1:
                path_found = path_found+1
                if path_found == 1:
                    path.append(bl)
                else:
                    new_path = path[:-1]
                    new_path.append(bl)
                    incompleted_paths.append(new_path)
            if (ll is not None) and (not self.findLoopInPath(path,ll)) and ll.getTd() < 1:
                path_found = path_found+1
                if path_found == 1:
                    path.append(ll)
                else:
                    new_path = path[:-1]
                    new_path.append(ll)
                    incompleted_paths.append(new_path)
            if (tl is not None) and (not self.findLoopInPath(path,tl)) and tl.getTd() < 1:
                path_found = path_found+1
                if path_found == 1:
                    path.append(tl)
                else:
                    new_path = path[:-1]
                    new_path.append(tl)
                    incompleted_paths.append(new_path)

            if path_found == 0:
                incompleted_paths.remove(path)
                completed_paths.append(path)

        # print(incompleted_paths)
        print(len(completed_paths))
        path_cnt = 0
        self.otherpathTbl.clearContents()
        self.otherpathTbl.setSortingEnabled(False)

        for p in completed_paths:
            path = Path()
            path.setId(path_cnt+1)
            for s in p:
                if path.getLength() == 0:
                    path.moveTo(s.rect().center())
                else:
                    path.lineTo(s.rect().center())
                    path.moveTo(s.rect().center())
                path.addCell(s)
            # self.scene.addPath(path,QPen(QColor(0,153,255,255),1,Qt.SolidLine),QBrush(Qt.NoBrush))
            self.otherpathTbl.insertRow(path_cnt)
            item0 = QTableWidgetItem()
            item0.setData(Qt.DisplayRole, path.getId())
            item1 = QTableWidgetItem()
            item1.setData(Qt.DisplayRole, path.getLength())
            item2 = QTableWidgetItem()
            item2.setData(Qt.DisplayRole, float(path.getDuration()))
            item3 = QTableWidgetItem()
            item3.setData(Qt.DisplayRole, float(path.getAggM()))
            self.otherpathTbl.setItem(path_cnt,0, item0)
            self.otherpathTbl.setItem(path_cnt,1, item1)
            self.otherpathTbl.setItem(path_cnt,2, item2)
            self.otherpathTbl.setItem(path_cnt,3, item3)
            self.possible_otherpaths["paths"].append(path)
            path_cnt = path_cnt + 1
        
        self.otherpathTbl.setSortingEnabled(True)
                

    def drawOtherPath(self):
        for p in self.possible_otherpaths["paths"]:
            item = p.getPathItem()
            if item is not None:
                self.scene.removeItem(item)
                p.setPathItem(None)

        for index in sorted(self.pathTbl.selectionModel().selectedRows()):
            row = index.row()
            id = int(self.pathTbl.item(row,0).text())
            path = [p for p in self.possible_otherpaths["paths"] if p.getId()==id] 
            if len(path)>0:
                # self.scene.removeItem(path[0])
                pathItem = self.scene.addPath(path[0],QPen(QColor(0,153,255,255),1,Qt.SolidLine),QBrush(Qt.NoBrush))
                path[0].setPathItem(pathItem)

            
    def findLoopInPath(self, path, segment):
        value = [d for d in path if d.getId()==segment.getId()]
        if len(value)>0:
            return True
        else:
            return False

    def findSegment(self, i,j):
        value = [d for d in self.segments["segments"] if d["row"]==i and d["col"]==j]
        #value = filter(lambda s: s[0] == key, self.segments["segments"])
        #print(len(value))
        if len(value)>0:
            return value[0]["obj"]
        else:
            return None
    
    def startSim(self):
        for s in self.patrollers["agents"]:
            startA = s.getStartLoc()
            s.setCurrentLoc(startA)
            s_node = s.getNode()
            s_node.setPos(0,0)

    # def pauseSim(self):

    # def resetSim(self):

    
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53,53,53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(15,15,15))
    palette.setColor(QPalette.AlternateBase, QColor(53,53,53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53,53,53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
         
    palette.setColor(QPalette.Highlight, QColor(142,45,197).lighter())
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    window = BorderSim()
    sys.exit(app.exec_())
