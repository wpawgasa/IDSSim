import csv
import sip
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from GridCell import *
from Agent import *
from Path import *
from FootprintSensor import *
from functools import partial
from dijkstra import Vertex, Graph, Dijkstra
from joblib import Parallel, delayed, parallel_backend
import pandas as pd
from random import shuffle, sample
import numpy as np

sip.setapi('QString', 2)
sip.setapi('QVariant', 2)


class SimScene(QGraphicsScene):
    cellEntered = pyqtSignal([QGraphicsItem], [QGraphicsWidget])
    cellLeave = pyqtSignal([QGraphicsItem], [QGraphicsWidget])


class BorderSim(QWidget):
    def __init__(self):
        super().__init__()

        self.number_row = 0
        self.number_col = 0

        self.patrols = []
        self.trespassers = []
        self.noises = []
        self.segments = []

        self.patrol_move_model = 0
        self.trespasser_move_model = [0.5, 0.5, 0.0]
        self.trespasser_arrival_rate = 0
        self.noise_rate = 0

        self.num_patrol = 0
        self.detection_coef = 1.00
        self.investigation_time = 0
        self.repeat_guard = 5
        self.comm_success_rate = 0.8
        self.allowed_no_fp_stages = 10
        self.mcts_simulations = 100
        self.planning_stages = 10

        self.entry_prob = []
        self.totalStat = 0
        # self.targetlifetime = 0.5 #target is active after time period

        self.number_t_entry = 0  # number of trespasser entering the area during the period
        self.number_n_entry = 0  # number of noise generated in the area during the period
        self.number_t_exit = 0  # number of trespasser exiting the area through the exit line
        # self.number_o_exit = 0
        self.number_t_detected = 0  # number of intruder detected by a sensors (true detection)
        self.number_n_detected = 0  # number of intruder detected by a sensors (false detection)
        self.trespasser_found = False
        self.accu_tres = 0
        self.avg_detection_rate = 0
        self.detection_rate_per_round = []
        self.result1_df = pd.DataFrame(columns=['entering', 'leaving', 'detected', 'detection_rate'])

        self.zoning = False
        self.zoning_scale = 0.8

        self.pos_x = 10
        self.pos_y = 35
        self.grid_width = 10
        self.region_center_x = 0
        self.region_center_y = 0

        self.num_period = 1
        self.period_len = 100
        self.stage_duration = 0.1

        self.timer = QTimer()
        self.curP = 1
        self.curT = 0
        self.timer.timeout.connect(self.simulate)

        layout = QHBoxLayout()
        self.sceneWidget = QWidget()
        self.setSimScene()
        tabView = self.createTabView()
        layout.addWidget(self.sceneWidget)
        layout.addWidget(tabView)
        self.setLayout(layout)
        self.setFixedSize(1400, 800)
        self.show()

    def setSimScene(self):
        self.font = QFont("Courier")
        self.font.setPointSize(8)
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
        self.scene.setBackgroundBrush(QColor(0, 0, 0, 255))
        self.scene.cellEntered.connect(self.handleCellEntered)
        self.scene.cellLeave.connect(self.handleCellLeave)

        self.infoscene = QGraphicsScene(self)
        self.infoscene.setBackgroundBrush(QColor(0, 0, 0, 255))

        self.display_row = self.infoscene.addText("Row: ")
        self.display_row.setPos(10, 5)
        self.display_row.setFont(self.font)
        self.display_col = self.infoscene.addText("Column: ")
        self.display_col.setPos(60, 5)
        self.display_col.setFont(self.font)
        self.display_td = self.infoscene.addText("Difficulty: ")
        self.display_td.setPos(140, 5)
        self.display_td.setFont(self.font)
        self.display_ob = self.infoscene.addText("Obscurity: ")
        self.display_ob.setPos(250, 5)
        self.display_ob.setFont(self.font)
        self.display_st = self.infoscene.addText("Statistic: ")
        self.display_st.setPos(350, 5)
        self.display_st.setFont(self.font)
        self.display_L = self.infoscene.addText("L: ")
        self.display_L.setPos(450, 5)
        self.display_L.setFont(self.font)
        self.display_zone = self.infoscene.addText("Zone: ")
        self.display_zone.setPos(505, 5)
        self.display_zone.setFont(self.font)

        self.display_row_val = self.infoscene.addText("-")
        self.display_row_val.setPos(40, 5)
        self.display_row_val.setFont(self.font)
        self.display_row_val.setDefaultTextColor(QColor(255, 255, 0, 255))
        self.display_col_val = self.infoscene.addText("-")
        self.display_col_val.setPos(120, 5)
        self.display_col_val.setFont(self.font)
        self.display_col_val.setDefaultTextColor(QColor(255, 255, 0, 255))
        self.display_td_val = self.infoscene.addText("-")
        self.display_td_val.setPos(220, 5)
        self.display_td_val.setFont(self.font)
        self.display_td_val.setDefaultTextColor(QColor(255, 0, 0, 255))
        self.display_ob_val = self.infoscene.addText("-")
        self.display_ob_val.setPos(320, 5)
        self.display_ob_val.setFont(self.font)
        self.display_ob_val.setDefaultTextColor(QColor(153, 0, 255, 255))
        self.display_st_val = self.infoscene.addText("-")
        self.display_st_val.setPos(420, 5)
        self.display_st_val.setFont(self.font)
        self.display_st_val.setDefaultTextColor(QColor(255, 0, 102, 255))
        self.display_L_val = self.infoscene.addText("-")
        self.display_L_val.setPos(470, 5)
        self.display_L_val.setFont(self.font)
        self.display_L_val.setDefaultTextColor(QColor(160, 167, 242, 255))
        self.display_zone_val = self.infoscene.addText("-")
        self.display_zone_val.setPos(535, 5)
        self.display_zone_val.setFont(self.font)
        self.display_zone_val.setDefaultTextColor(QColor(242, 160, 209, 255))

        self.display_cur_period = self.infoscene.addText("Period: ")
        self.display_cur_period.setPos(10, 16)
        self.display_cur_period.setFont(self.font)

        self.display_cur_stage = self.infoscene.addText("Stage: ")
        self.display_cur_stage.setPos(100, 16)
        self.display_cur_stage.setFont(self.font)

        self.display_sim_status = self.infoscene.addText("Status: ")
        self.display_sim_status.setPos(200, 16)
        self.display_sim_status.setFont(self.font)

        self.display_cur_period_val = self.infoscene.addText("0")
        self.display_cur_period_val.setPos(60, 16)
        self.display_cur_period_val.setFont(self.font)
        self.display_cur_period_val.setDefaultTextColor(QColor(197, 247, 126, 255))

        self.display_cur_stage_val = self.infoscene.addText("0")
        self.display_cur_stage_val.setPos(160, 16)
        self.display_cur_stage_val.setFont(self.font)
        self.display_cur_stage_val.setDefaultTextColor(QColor(197, 247, 126, 255))

        self.display_sim_status_val = self.infoscene.addText("Stopped")
        self.display_sim_status_val.setPos(260, 16)
        self.display_sim_status_val.setFont(self.font)
        self.display_sim_status_val.setDefaultTextColor(QColor(224, 173, 247, 255))

        self.view_0 = QGraphicsView(self)
        self.view_0.setFixedSize(630, 40)
        self.view_0.setSceneRect(0, 0, 630, 40)

        self.view_0.fitInView(0, 0, 630, 40, Qt.KeepAspectRatio)

        self.view_0.setScene(self.infoscene)
        self.view_0.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view_0.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.view_1 = QGraphicsView(self)
        self.view_1.setFixedSize(630, 720)
        # self.view_1.setSceneRect(0,0,800,1000)

        self.view_1.fitInView(0, 0, 630, 720, Qt.KeepAspectRatio)

        self.view_1.setScene(self.scene)
        self.view_1.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view_1.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        layout = QVBoxLayout()
        layout.addWidget(self.view_0)
        layout.addWidget(self.view_1)
        self.sceneWidget.setLayout(layout)
        self.sceneWidget.setFixedSize(630, 780)

    def handleCellEntered(self, cell):
        # print(cell.getId())
        self.display_row_val.setPlainText(str(np.around(cell.getRow(), decimals=2)))
        self.display_col_val.setPlainText(str(np.around(cell.getCol(), decimals=2)))
        self.display_td_val.setPlainText(str(np.around(cell.getTd(), decimals=2)))
        self.display_ob_val.setPlainText(str(np.around(cell.getOb(), decimals=2)))
        self.display_st_val.setPlainText(str(np.around(cell.getSt(), decimals=2)))
        self.display_L_val.setPlainText(str(np.around(cell.getL(), decimals=2)))
        self.display_zone_val.setPlainText(cell.getZone())

    def handleCellLeave(self, cell):
        # print(cell.getId())
        self.display_row_val.setPlainText("-")
        self.display_col_val.setPlainText("-")
        self.display_td_val.setPlainText("-")
        self.display_ob_val.setPlainText("-")
        self.display_st_val.setPlainText("-")
        self.display_L_val.setPlainText("-")
        self.display_zone_val.setPlainText("-")

    def createTabView(self):
        tabView = QTabWidget()
        envSettingTab = QWidget()
        agentSettingTab = QWidget()
        footprintSettingTab = QWidget()
        simCtrlTab = QWidget()
        resultTab = QWidget()

        tabView.addTab(envSettingTab, "Environment")
        tabView.addTab(agentSettingTab, "Agents")
        tabView.addTab(footprintSettingTab, "Footprint")
        tabView.addTab(simCtrlTab, "Simulation")
        tabView.addTab(resultTab, "Result")
        envLayOut = self.createEnvSettingLayOut()
        envSettingTab.setLayout(envLayOut)
        agentLayOut = self.createAgentSettingLayOut()
        agentSettingTab.setLayout(agentLayOut)
        simLayOut = self.createSimCtrlLayOut()
        simCtrlTab.setLayout(simLayOut)
        resultLayOut = self.createResultLayOut()
        resultTab.setLayout(resultLayOut)
        fpLayOut = self.createFootprintSettingLayOut()
        footprintSettingTab.setLayout(fpLayOut)

        return tabView

    def createEnvSettingLayOut(self):
        layout = QFormLayout()
        dimension = QHBoxLayout()
        dimensionW = QSpinBox()
        dimensionW.setRange(0, 500)
        dimensionW.valueChanged.connect(self.onColChanged)
        dimensionH = QSpinBox()
        dimensionH.setRange(0, 1000)
        dimensionH.valueChanged.connect(self.onRowChanged)
        WLabel = QLabel("Columns (Width)")
        HLabel = QLabel("Rows (Height)")
        dimension.addWidget(WLabel)
        dimension.addWidget(dimensionW)
        dimension.addWidget(HLabel)
        dimension.addWidget(dimensionH)
        layout.addRow("Region Dimension:", dimension)
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

        box2Layout = QHBoxLayout()

        areaViewLayout = QHBoxLayout()
        areaViewLabel = QLabel("View Selection")
        viewSelNone = QRadioButton("None")
        viewSelNone.setChecked(True)
        viewTress = QRadioButton("Trespassability")
        viewSelTD = QRadioButton("Difficulty")
        viewSelOB = QRadioButton("Obscurity")
        viewSelST = QRadioButton("Statistic")
        viewScore = QRadioButton("Score")
        viewSelNone.toggled.connect(self.changeToNoneView)
        viewTress.toggled.connect(self.changeToTresView)
        viewSelTD.toggled.connect(self.changeToTDView)
        viewSelOB.toggled.connect(self.changeToOBView)
        viewSelST.toggled.connect(self.changeToSTView)
        viewScore.toggled.connect(self.changeToScoreView)

        areaViewLayout.addWidget(areaViewLabel)
        areaViewLayout.addWidget(viewSelNone)
        areaViewLayout.addWidget(viewTress)
        areaViewLayout.addWidget(viewSelTD)
        areaViewLayout.addWidget(viewSelOB)
        areaViewLayout.addWidget(viewSelST)
        areaViewLayout.addWidget(viewScore)
        areaViewLayout.setAlignment(Qt.AlignLeft)

        box2Layout.addLayout(areaViewLayout)

        layout.addRow(box2Layout)

        # box3Layout = QHBoxLayout()

        # pathViewLayout = QVBoxLayout()

        # calPathBtn = QPushButton("Determine Possible Crossing Paths")
        # viewPath = QCheckBox("Show Paths")
        # viewPath.setChecked(True)
        # calPathBtn.clicked.connect(self.calPaths)
        # pathViewLayout.addWidget(calPathBtn)
        # pathViewLayout.addWidget(viewPath)
        # self.pathTbl = QTableWidget(0,4)
        # header_labels = ['Path', 'Length', 'Duration', 'Significance']
        # self.pathTbl.setHorizontalHeaderLabels(header_labels)
        # self.pathTbl.setFixedSize(500,300)
        # self.pathTbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.pathTbl.setSelectionMode(QAbstractItemView.MultiSelection)
        # self.pathTbl.setStyleSheet("QTableWidget::item:selected{ background-color: red }")
        # self.pathTbl.itemSelectionChanged.connect(self.drawPath)
        # self.pathTbl.setSortingEnabled(True)

        # pathViewLayout.addWidget(self.pathTbl)

        # otherpathViewLayout = QVBoxLayout()

        # calOtherPathBtn = QPushButton("Determine Possible Non-crossing Paths")
        # viewPath = QCheckBox("Show Paths")
        # viewPath.setChecked(True)
        # calOtherPathBtn.clicked.connect(self.calOtherPaths)
        # otherpathViewLayout.addWidget(calOtherPathBtn)
        # pathViewLayout.addWidget(viewPath)
        # self.otherpathTbl = QTableWidget(0,4)
        # header_labels = ['Path', 'Length', 'Duration', 'Significance']
        # self.otherpathTbl.setHorizontalHeaderLabels(header_labels)
        # self.otherpathTbl.setFixedSize(500,300)
        # self.otherpathTbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.otherpathTbl.setSelectionMode(QAbstractItemView.MultiSelection)
        # self.otherpathTbl.setStyleSheet("QTableWidget::item:selected{ background-color: yellow }")
        # self.otherpathTbl.itemSelectionChanged.connect(self.drawOtherPath)
        # self.pathTbl.setSortingEnabled(True)

        # otherpathViewLayout.addWidget(self.otherpathTbl)

        # box3Layout.addLayout(pathViewLayout)
        # box3Layout.addLayout(otherpathViewLayout)

        # layout.addRow(box3Layout)

        return layout

    def createAgentSettingLayOut(self):
        layout = QVBoxLayout()
        # trespasserLayout = QHBoxLayout()
        # patrollerLayout = QHBoxLayout()

        trespasserGroupBox = QGroupBox("Trespasser Agent")
        trespasserLayout = QFormLayout()
        # trespasserArrModel = QHBoxLayout()
        # poissonArr = QRadioButton("Poisson")
        # paretoArr = QRadioButton("Pareto")
        # poissonArr.setChecked(True)
        # intruderArrModel.addWidget(poissonArr)
        # intruderArrModel.addWidget(paretoArr)
        # intruderLayout.addRow("Arrival Model: ", intruderArrModel)

        trespasserArrRate = QSpinBox()
        trespasserArrRate.setRange(0, 100)
        trespasserArrRate.setSingleStep(1)
        trespasserArrRate.setValue(0)
        trespasserArrRate.valueChanged.connect(self.setTrespasserArrivalRate)
        trespasserLayout.addRow("Arrival Rate: ", trespasserArrRate)

        trespasserRandomRatio = QSpinBox()
        trespasserRandomRatio.setRange(0, 100)
        trespasserRandomRatio.setSingleStep(1)
        trespasserRandomRatio.setValue(50)
        trespasserRandomRatio.valueChanged.connect(self.setTrespasserMovementModel1)
        trespasserLayout.addRow("% of random moving trespasser: ", trespasserRandomRatio)
        trespasserStaticEnvBasedRatio = QSpinBox()
        trespasserStaticEnvBasedRatio.setRange(0, 100)
        trespasserStaticEnvBasedRatio.setSingleStep(1)
        trespasserStaticEnvBasedRatio.setValue(50)
        trespasserStaticEnvBasedRatio.valueChanged.connect(self.setTrespasserMovementModel2)
        trespasserLayout.addRow("% of static environment-based moving trespasser: ", trespasserStaticEnvBasedRatio)
        trespasserDynamicEnvBasedRatio = QSpinBox()
        trespasserDynamicEnvBasedRatio.setRange(0, 100)
        trespasserDynamicEnvBasedRatio.setSingleStep(1)
        trespasserDynamicEnvBasedRatio.setValue(0)
        trespasserDynamicEnvBasedRatio.valueChanged.connect(self.setTrespasserMovementModel3)
        trespasserLayout.addRow("% of dynamic environment-based moving trespasser: ", trespasserDynamicEnvBasedRatio)

        # trespasserMovementModel = QComboBox()
        # trespasserMovementModel.addItem("Random Movement", 0)
        # trespasserMovementModel.addItem("Static Environment based", 1)
        # trespasserMovementModel.addItem("Dynamic Environment based", 2)
        # trespasserMovementModel.currentIndexChanged.connect(self.setTrespasserMovementModel)
        # trespasserLayout.addRow("Movement Model: ", trespasserMovementModel)

        # noiseGroupBox = QGroupBox("Noise")
        # noiseLayout = QFormLayout()
        noiseRate = QSpinBox()
        noiseRate.setRange(0, 100)
        noiseRate.setSingleStep(1)
        noiseRate.setValue(0)
        noiseRate.valueChanged.connect(self.setNoiseRate)
        trespasserLayout.addRow("% of Noise-to-trespasser: ", noiseRate)
        # noiseGroupBox.setLayout(noiseLayout)
        trespasserGroupBox.setLayout(trespasserLayout)
        layout.addWidget(trespasserGroupBox)
        # layout.addWidget(noiseGroupBox)

        patrollerGroupBox = QGroupBox("Patrol Agent")
        patrollerLayout = QFormLayout()

        patrollerNumber = QSpinBox()
        patrollerNumber.setRange(0, 100)
        patrollerNumber.setSingleStep(1)
        patrollerNumber.setValue(0)
        patrollerNumber.valueChanged.connect(self.setPatrolNumber)
        patrollerLayout.addRow("Number of patrols: ", patrollerNumber)

        detectionCoef = QDoubleSpinBox()
        detectionCoef.setRange(0.00, 1.00)
        detectionCoef.setSingleStep(0.01)
        detectionCoef.setDecimals(2)
        detectionCoef.setValue(1.00)
        detectionCoef.valueChanged.connect(self.setDetectionCoef)
        patrollerLayout.addRow("Detection Coefficient: ", detectionCoef)

        investigationTime = QSpinBox()
        investigationTime.setRange(0, 100)
        investigationTime.setSingleStep(1)
        investigationTime.setValue(0)
        investigationTime.valueChanged.connect(self.setInvestigationTime)
        patrollerLayout.addRow("Investigation time: ", investigationTime)

        commSuccessRate = QDoubleSpinBox()
        commSuccessRate.setRange(0.0, 1.0)
        commSuccessRate.setSingleStep(0.1)
        commSuccessRate.setDecimals(1)
        commSuccessRate.setValue(0.8)
        commSuccessRate.valueChanged.connect(self.setCommSuccessRate)
        patrollerLayout.addRow("Communication Success Rate: ", commSuccessRate)

        planningStages = QSpinBox()
        planningStages.setRange(0, 100)
        planningStages.setSingleStep(1)
        planningStages.setValue(10)
        planningStages.valueChanged.connect(self.setPlanningStages)
        patrollerLayout.addRow("Length of each planning cycle (stages): ", planningStages)

        repeatGuard = QSpinBox()
        repeatGuard.setRange(0, 100)
        repeatGuard.setSingleStep(1)
        repeatGuard.setValue(5)
        repeatGuard.valueChanged.connect(self.setRepeatGuard)
        patrollerLayout.addRow("Re-patrol guard (stages): ", repeatGuard)

        allowNoFP = QSpinBox()
        allowNoFP.setRange(0, 100)
        allowNoFP.setSingleStep(5)
        allowNoFP.setValue(10)
        allowNoFP.valueChanged.connect(self.setAllowNoFP)
        patrollerLayout.addRow("Allowed # of stages for no reported footprint on each fp sensor: ", allowNoFP)

        MCTSSimRounds = QSpinBox()
        MCTSSimRounds.setRange(10, 1000)
        MCTSSimRounds.setSingleStep(10)
        MCTSSimRounds.setValue(100)
        MCTSSimRounds.valueChanged.connect(self.setMCTSRounds)
        patrollerLayout.addRow("# of MCTS rounds per planning: ", MCTSSimRounds)

        patrollerMovementModel = QComboBox()
        patrollerMovementModel.addItem("Random", 0)
        patrollerMovementModel.addItem("Single Barrier", 1)
        patrollerMovementModel.addItem("Double Barrier", 2)
        patrollerMovementModel.addItem("Heuristic Planning", 3)
        patrollerMovementModel.addItem("POMDP Planning", 4)
        patrollerMovementModel.currentIndexChanged.connect(self.setPatrolMovementModel)
        patrollerLayout.addRow("Movement Model: ", patrollerMovementModel)

        patrollerZoning = QCheckBox("Apply zoning to random, heuristic planning and POMDP planning")
        patrollerZoning.stateChanged.connect(lambda: self.setZoning(patrollerZoning))
        patrollerLayout.addRow(patrollerZoning)
        placePatroller = QPushButton("Place Patrollers")
        placePatroller.clicked.connect(self.placePatrols)
        patrollerLayout.addRow(placePatroller)

        zoningScale = QDoubleSpinBox()
        zoningScale.setRange(0.0, 1.0)
        zoningScale.setSingleStep(0.1)
        zoningScale.setDecimals(1)
        zoningScale.setValue(0.8)
        zoningScale.valueChanged.connect(self.setZoningScale)
        patrollerLayout.addRow("Zoning Scale: ", zoningScale)

        patrollerGroupBox.setLayout(patrollerLayout)

        layout.addWidget(patrollerGroupBox)
        return layout

    def createFootprintSettingLayOut(self):
        layout = QVBoxLayout()

        selffpSensorGroupBox = QGroupBox("Self Footprint Sensor")
        selffpSensorLayOut = QFormLayout()
        equipFPSensorBtn = QPushButton("Equip fp sensor to each border patrol")
        equipFPSensorBtn.clicked.connect(self.equipFPSensor)
        selffpSensorLayOut.addRow(equipFPSensorBtn)
        stripoffFPSensorBtn = QPushButton("Strip off fp sensor from each border patrol")
        stripoffFPSensorBtn.clicked.connect(self.stripoffFPSensor)
        selffpSensorLayOut.addRow(stripoffFPSensorBtn)

        selffpSensorGroupBox.setLayout(selffpSensorLayOut)

        layout.addWidget(selffpSensorGroupBox)

        return layout

    def createResultLayOut(self):
        layout = QVBoxLayout()

        result1GroupBox = QGroupBox("Trespasser Detection Rate")
        result1LayOut = QFormLayout()

        self.result1Tbl = QTableWidget(0, 5)
        result1_header_labels = ['Round', 'Entering Trespasser', 'Leaving Trespasser', 'Detected Trespasser',
                                 'Detection Rate']
        self.result1Tbl.setHorizontalHeaderLabels(result1_header_labels)
        self.result1Tbl.setFixedSize(650, 300)
        self.result1Tbl.setColumnWidth(0, 50)
        self.result1Tbl.setColumnWidth(1, 150)
        self.result1Tbl.setColumnWidth(2, 150)
        self.result1Tbl.setColumnWidth(3, 150)
        self.result1Tbl.setColumnWidth(4, 150)
        self.result1Tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result1Tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        # self.result1Tbl.setStyleSheet("QTableWidget::item:selected{ background-color: #fcba03}")
        # self.pathTbl.itemSelectionChanged.connect(self.drawPath)
        # self.result1Tbl.setSortingEnabled(True)

        result1LayOut.addRow(self.result1Tbl)

        self.avgResult1 = QLabel(str(0))

        result1LayOut.addRow("Average trespasser detection rate: ", self.avgResult1)

        exportButton = QPushButton("Export result to .csv")
        exportButton.clicked.connect(self.exportResult)
        result1LayOut.addRow(exportButton)

        result1GroupBox.setLayout(result1LayOut)

        layout.addWidget(result1GroupBox)

        return layout

    def equipFPSensor(self):
        for p in self.patrols:
            fp_sensor = FootprintSensor(p.getCurLoc(), p.getId(),
                                        self.pos_x + (int(p.getCurLoc().getCol()) - 1) * self.grid_width + self.grid_width*0.25,
                                        self.pos_y + (int(p.getCurLoc().getRow()) - 1) * self.grid_width + self.grid_width*0.25,
                                        self.grid_width*0.5, self.grid_width*0.5
                                        )
            p.setFPSensor(fp_sensor)
            self.scene.addItem(fp_sensor)

    def stripoffFPSensor(self):
        for p in self.patrols:
            fp_sensor = p.getFPSensor()
            self.scene.removeItem(fp_sensor)
            p.setFPSensor(None)

    def setZoningScale(self, v):
        self.zoning_scale = v

    def setTrespasserArrivalRate(self, v):
        self.trespasser_arrival_rate = v

    def setNoiseRate(self, v):
        self.noise_rate = v

    def setDetectionCoef(self, v):
        self.detection_coef = v

    def setInvestigationTime(self, v):
        self.investigation_time = v

    def setRepeatGuard(self, v):
        self.repeat_guard = v

    def setCommSuccessRate(self, v):
        self.comm_success_rate = v

    def setAllowNoFP(self, v):
        self.allowed_no_fp_stages = v

    def setMCTSRounds(self, v):
        self.mcts_simulations = v

    def setTrespasserMovementModel1(self, v):
        self.trespasser_move_model[0] = v / 100

    def setTrespasserMovementModel2(self, v):
        self.trespasser_move_model[1] = v / 100

    def setTrespasserMovementModel3(self, v):
        self.trespasser_move_model[2] = v / 100

    def setPatrolMovementModel(self, v):
        self.patrol_move_model = v
        print("Patrol movement model is set to %i" % v)

    def setPlanningStages(self, v):
        self.planning_stages = v

    def setPatrolNumber(self, v):
        self.num_patrol = v

    def setZoning(self, b):
        if b.isChecked() == True:
            self.zoning = True
        else:
            self.zoning = False

    def exportResult(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "All Files (*);;Text Files (*.csv)", options=options)
        if fileName:
            self.result1_df.to_csv(fileName, sep=",", header=True, index=False)

    def createSimCtrlLayOut(self):
        layout = QFormLayout()
        numPeriod = QSpinBox()
        numPeriod.setRange(0, 500)
        numPeriod.setSingleStep(1)
        numPeriod.setValue(1)
        numPeriod.valueChanged.connect(self.onNumPeriodChanged)
        layout.addRow("Number of operation periods", numPeriod)
        numStages = QSpinBox()
        numStages.setRange(0, 5000)
        numStages.setSingleStep(10)
        numStages.setValue(100)
        numStages.valueChanged.connect(self.onPeriodLengthChanged)
        layout.addRow("Number of time stages per operation", numStages)
        stageDuration = QDoubleSpinBox()
        stageDuration.setRange(0, 1)
        stageDuration.setSingleStep(0.01)
        stageDuration.setValue(0.1)
        stageDuration.valueChanged.connect(self.onStageDurationChanged)
        layout.addRow("Time Stage Duration (ms)", stageDuration)

        simcontrolBtn = QHBoxLayout()
        self.runButton = QPushButton("Run Simulation")
        self.runButton.clicked.connect(self.startSim)
        self.pauseButton = QPushButton("Pause Simulation")
        self.pauseButton.clicked.connect(self.pauseSim)
        self.resumeButton = QPushButton("Resume Simulation")
        self.resumeButton.clicked.connect(self.resumeSim)
        self.resetButton = QPushButton("Reset Simulation")
        self.resetButton.clicked.connect(self.resetSim)
        self.stopButton = QPushButton("Stop Simulation")
        self.stopButton.clicked.connect(self.stopSim)
        self.pauseButton.setDisabled(True)
        self.resumeButton.setDisabled(True)
        self.resetButton.setDisabled(True)
        self.stopButton.setDisabled(True)
        simcontrolBtn.addWidget(self.runButton)
        simcontrolBtn.addWidget(self.pauseButton)
        simcontrolBtn.addWidget(self.resumeButton)
        simcontrolBtn.addWidget(self.resetButton)
        simcontrolBtn.addWidget(self.stopButton)
        layout.addRow(simcontrolBtn)

        # simStatusGroupBox = QGroupBox("Simulation Status")
        # simStatusLayout = QHBoxLayout()
        # simCurrentPeriodLabel = QLabel("Current Period")
        # simCurrentPeriod = QLabel(str(0))
        # simCurrentStageLabel = QLabel("Current Stage")
        # simCurrentStage = QLabel(str(0))
        # simStatusLayout.addWidget(simCurrentPeriodLabel)
        # simStatusLayout.addWidget(simCurrentPeriod)
        # simStatusLayout.addWidget(simCurrentStageLabel)
        # simStatusLayout.addWidget(simCurrentStage)
        # simStatusGroupBox.setLayout(simStatusLayout)
        #
        # layout.addRow(simStatusGroupBox)

        return layout

    def onRowChanged(self, value):
        self.number_row = value

    def onColChanged(self, value):
        self.number_col = value

    def onNumPeriodChanged(self, value):
        self.num_period = value

    def onPeriodLengthChanged(self, value):
        self.period_len = value

    def onStageDurationChanged(self, value):
        self.stage_duration = value

    def drawGrid(self):

        for s in self.segments:
            self.scene.removeItem(s["obj"])

        self.segments = []
        # while self.grid_width*self.number_col > 480:
        #     self.grid_width = self.grid_width*0.95

        for j in range(0, self.number_row):

            for i in range(0, self.number_col):

                segment = GridCell(self.pos_x + i * self.grid_width, self.pos_y + j * self.grid_width,
                                   self.grid_width, self.grid_width)

                segment.setPen(QColor(Qt.white))
                segment.setBrush(QBrush(Qt.NoBrush))

                self.scene.addItem(segment)

                # segment = GridCell(j+1,i+1,rect)
                segment.setRow(j + 1)
                segment.setCol(i + 1)
                segment.setId("Cell_" + str(j + 1) + "_" + str(i + 1))
                if i == 0:
                    segment.setEntry(True)
                elif i == self.number_col - 1:
                    segment.setExit(True)
                segment.calScore(self.accu_tres)

                # rect.setToolTip("td: %f ob: %f st: %f de: %f m: %f" %
                #     (segment.getTd(),segment.getOb(),segment.getSt(),segment.getDe(),segment.getM()))
                # self.segments.append(segment)
                self.segments.append({"row": j + 1, "col": i + 1, "key": segment.getId(), "obj": segment})

        self.region_center_x = int(np.ceil(self.number_col / 2))
        self.region_center_y = int(np.ceil(self.number_row / 2))
        self.view_1.setSceneRect(0, 0, (self.number_col + 5) * self.grid_width, (self.number_row + 5) * self.grid_width)
        self.view_1.setScene(self.scene)

    # def sumSt(self):
    #     return sum(x["obj"].getSt() for x in self.segments["segments"])

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
                    if i_row <= self.number_row:
                        for field in row:
                            if i_col <= self.number_col:
                                # s = self.findSegment(i_row,i_col)
                                s = self.segments[d]["obj"]
                                # print("%i %i" % (i_row,i_col))
                                s.setTd(float(field))
                                s.calScore(self.accu_tres)
                                i_col = i_col + 1
                                d = d + 1
                        i_row = i_row + 1
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
                    if i_row <= self.number_row:
                        for field in row:
                            if i_col <= self.number_col:
                                s = self.segments[d]["obj"]
                                # print("%i %i" % (i_row,i_col))
                                s.setOb(float(field))
                                s.calScore(self.accu_tres)
                                d = d + 1
                                i_col = i_col + 1
                        i_row = i_row + 1
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
                    if i_row == 1:
                        self.accu_tres = float(row[0])

                    if 1 < i_row <= self.number_row:
                        for field in row:
                            if i_col <= self.number_col:
                                s = self.segments[d]["obj"]
                                # print("%i %i" % (i_row,i_col))
                                s.setSt(float(field))
                                s.calScore(self.accu_tres)
                                d = d + 1
                                i_col = i_col + 1
                        i_col = 1
                    i_row = i_row + 1

    def changeToNoneView(self):
        # print('none')
        if not self.segments:
            # print('empty')
            return

        for d in self.segments:
            segment = d["obj"]
            red = 0
            green = 0
            blue = 0
            alpha = 0
            segment.setBrush(QColor(red, green, blue, alpha))

    def changeToTresView(self):
        # print('td')
        if not self.segments:
            return

        for d in self.segments:
            segment = d["obj"]
            red = 150
            green = 150
            blue = 150
            alpha = 0 if segment.getTd() < 1 else 255
            segment.setBrush(QColor(red, green, blue, alpha))

    def changeToTDView(self):
        # print('td')
        if not self.segments:
            return

        for d in self.segments:
            segment = d["obj"]
            if segment.getTd() < 1:
                red = 255
                green = 0
                blue = 0
                alpha = 255 * segment.getTd()
                segment.setBrush(QColor(red, green, blue, alpha))

    def changeToOBView(self):
        if not self.segments:
            return

        for d in self.segments:
            segment = d["obj"]
            if segment.getOb() < 1:
                red = 150
                green = 0
                blue = 255
                alpha = 255 * segment.getOb()
                segment.setBrush(QColor(red, green, blue, alpha))

    def changeToSTView(self):
        if not self.segments:
            return

        for d in self.segments:
            segment = d["obj"]
            if segment.getSt() > 0:
                red = 50
                green = 150
                blue = 85
                alpha = 255 - int(np.ceil((self.accu_tres - segment.getSt()) * self.accu_tres / 255))
                segment.setBrush(QColor(red, green, blue, alpha))

    def changeToScoreView(self):
        # print('td')
        if not self.segments:
            return
        max_L = max([s["obj"].getL() for s in self.segments])
        for d in self.segments:
            segment = d["obj"]
            if segment.getL() > 0:
                red = 180
                green = 30
                blue = 100
                alpha = 150 * segment.getL() / max_L
                segment.setBrush(QColor(red, green, blue, alpha))

    def calPaths(self):
        if not self.segments:
            return
        entries = []
        for d in self.segments:
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

                tt = self.findSegment(endpoint.getRow() - 1, endpoint.getCol())
                tr = self.findSegment(endpoint.getRow() - 1, endpoint.getCol() + 1)
                rr = self.findSegment(endpoint.getRow(), endpoint.getCol() + 1)
                br = self.findSegment(endpoint.getRow() + 1, endpoint.getCol() + 1)
                bb = self.findSegment(endpoint.getRow() + 1, endpoint.getCol())
                bl = self.findSegment(endpoint.getRow() + 1, endpoint.getCol() - 1)
                ll = self.findSegment(endpoint.getRow(), endpoint.getCol() - 1)
                tl = self.findSegment(endpoint.getRow() - 1, endpoint.getCol() - 1)
                path_found = 0
                if (tt is not None) and (not self.findLoopInPath(path, tt)) and tt.getTd() < 1:
                    path_found = path_found + 1
                    if path_found == 1:
                        path.append(tt)
                    else:
                        new_path = path[:-1]
                        new_path.append(tt)
                        incompleted_paths.append(new_path)

                if (tr is not None) and (not self.findLoopInPath(path, tr)) and tr.getTd() < 1:
                    path_found = path_found + 1
                    if path_found == 1:
                        path.append(tr)
                    else:
                        new_path = path[:-1]
                        new_path.append(tr)
                        incompleted_paths.append(new_path)

                if (rr is not None) and (not self.findLoopInPath(path, rr)) and rr.getTd() < 1:
                    path_found = path_found + 1
                    if path_found == 1:
                        path.append(rr)
                    else:
                        new_path = path[:-1]
                        new_path.append(rr)
                        incompleted_paths.append(new_path)
                if (br is not None) and (not self.findLoopInPath(path, br)) and br.getTd() < 1:
                    path_found = path_found + 1
                    if path_found == 1:
                        path.append(br)
                    else:
                        new_path = path[:-1]
                        new_path.append(br)
                        incompleted_paths.append(new_path)
                if (bb is not None) and (not self.findLoopInPath(path, bb)) and bb.getTd() < 1:
                    path_found = path_found + 1
                    if path_found == 1:
                        path.append(bb)
                    else:
                        new_path = path[:-1]
                        new_path.append(bb)
                        incompleted_paths.append(new_path)
                if (bl is not None) and (not self.findLoopInPath(path, bl)) and bl.getTd() < 1:
                    path_found = path_found + 1
                    if path_found == 1:
                        path.append(bl)
                    else:
                        new_path = path[:-1]
                        new_path.append(bl)
                        incompleted_paths.append(new_path)
                if (ll is not None) and (not self.findLoopInPath(path, ll)) and ll.getTd() < 1:
                    path_found = path_found + 1
                    if path_found == 1:
                        path.append(ll)
                    else:
                        new_path = path[:-1]
                        new_path.append(ll)
                        incompleted_paths.append(new_path)
                if (tl is not None) and (not self.findLoopInPath(path, tl)) and tl.getTd() < 1:
                    path_found = path_found + 1
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
            path.setId(path_cnt + 1)
            for s in p:
                if path.getLength() == 0:
                    path.moveTo(s.rect().center())
                else:
                    path.lineTo(s.rect().center())
                    path.moveTo(s.rect().center())
                path.addCell(s)
            # self.scene.addPath(path,QPen(QColor(0,153,255,255),1,Qt.SolidLine),QBrush(Qt.NoBrush))
            path.aggregateM(self.w_td, self.w_ob, self.w_st)
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
            self.pathTbl.setItem(path_cnt, 0, item0)
            self.pathTbl.setItem(path_cnt, 1, item1)
            self.pathTbl.setItem(path_cnt, 2, item2)
            self.pathTbl.setItem(path_cnt, 3, item3)
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
            id = int(self.pathTbl.item(row, 0).text())
            path = [p for p in self.possible_paths["paths"] if p.getId() == id]
            if len(path) > 0:
                # self.scene.removeItem(path[0])
                pathItem = self.scene.addPath(path[0], QPen(QColor(255, 0, 0, 255), 1, Qt.SolidLine),
                                              QBrush(Qt.NoBrush))
                path[0].setPathItem(pathItem)

    def calOtherPaths(self):
        if not self.segments:
            return
        entries = []
        for d in self.segments:
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

            tt = self.findSegment(endpoint.getRow() - 1, endpoint.getCol())
            tr = self.findSegment(endpoint.getRow() - 1, endpoint.getCol() + 1)
            rr = self.findSegment(endpoint.getRow(), endpoint.getCol() + 1)
            br = self.findSegment(endpoint.getRow() + 1, endpoint.getCol() + 1)
            bb = self.findSegment(endpoint.getRow() + 1, endpoint.getCol())
            bl = self.findSegment(endpoint.getRow() + 1, endpoint.getCol() - 1)
            ll = self.findSegment(endpoint.getRow(), endpoint.getCol() - 1)
            tl = self.findSegment(endpoint.getRow() - 1, endpoint.getCol() - 1)
            path_found = 0
            if (tt is not None) and (not self.findLoopInPath(path, tt)) and tt.getTd() < 1:
                path_found = path_found + 1
                if path_found == 1:
                    path.append(tt)
                else:
                    new_path = path[:-1]
                    new_path.append(tt)
                    incompleted_paths.append(new_path)

            if (tr is not None) and (not self.findLoopInPath(path, tr)) and tr.getTd() < 1:
                path_found = path_found + 1
                if path_found == 1:
                    path.append(tr)
                else:
                    new_path = path[:-1]
                    new_path.append(tr)
                    incompleted_paths.append(new_path)

            if (rr is not None) and (not self.findLoopInPath(path, rr)) and rr.getTd() < 1:
                path_found = path_found + 1
                if path_found == 1:
                    path.append(rr)
                else:
                    new_path = path[:-1]
                    new_path.append(rr)
                    incompleted_paths.append(new_path)
            if (br is not None) and (not self.findLoopInPath(path, br)) and br.getTd() < 1:
                path_found = path_found + 1
                if path_found == 1:
                    path.append(br)
                else:
                    new_path = path[:-1]
                    new_path.append(br)
                    incompleted_paths.append(new_path)
            if (bb is not None) and (not self.findLoopInPath(path, bb)) and bb.getTd() < 1:
                path_found = path_found + 1
                if path_found == 1:
                    path.append(bb)
                else:
                    new_path = path[:-1]
                    new_path.append(bb)
                    incompleted_paths.append(new_path)
            if (bl is not None) and (not self.findLoopInPath(path, bl)) and bl.getTd() < 1:
                path_found = path_found + 1
                if path_found == 1:
                    path.append(bl)
                else:
                    new_path = path[:-1]
                    new_path.append(bl)
                    incompleted_paths.append(new_path)
            if (ll is not None) and (not self.findLoopInPath(path, ll)) and ll.getTd() < 1:
                path_found = path_found + 1
                if path_found == 1:
                    path.append(ll)
                else:
                    new_path = path[:-1]
                    new_path.append(ll)
                    incompleted_paths.append(new_path)
            if (tl is not None) and (not self.findLoopInPath(path, tl)) and tl.getTd() < 1:
                path_found = path_found + 1
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
            path.setId(path_cnt + 1)
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
            self.otherpathTbl.setItem(path_cnt, 0, item0)
            self.otherpathTbl.setItem(path_cnt, 1, item1)
            self.otherpathTbl.setItem(path_cnt, 2, item2)
            self.otherpathTbl.setItem(path_cnt, 3, item3)
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
            id = int(self.pathTbl.item(row, 0).text())
            path = [p for p in self.possible_otherpaths["paths"] if p.getId() == id]
            if len(path) > 0:
                # self.scene.removeItem(path[0])
                pathItem = self.scene.addPath(path[0], QPen(QColor(0, 153, 255, 255), 1, Qt.SolidLine),
                                              QBrush(Qt.NoBrush))
                path[0].setPathItem(pathItem)

    def findLoopInPath(self, path, segment):
        value = [d for d in path if d.getId() == segment.getId()]
        if len(value) > 0:
            return True
        else:
            return False

    def placePatrols(self):
        if self.patrols:
            for p in self.patrols:
                if p.getFPSensor():
                    self.scene.removeItem(p.getFPSensor())
                self.scene.removeItem(p)
            self.patrols = []
        print("Number of patrols %i" % self.num_patrol)
        print("Is zoning %s" % self.zoning)
        if not self.segments:
            print("segments is empty")
            return

        if self.patrol_move_model == 0:
            if self.zoning:
                self.placeInZone2()
            else:
                self.placeRandom()
        elif self.patrol_move_model == 1:
            self.placeOnMiddleLine()
        elif self.patrol_move_model == 2:
            self.placeOnDoubleLines()
        elif self.patrol_move_model == 3 or self.patrol_move_model == 4:
            if self.zoning:
                self.placeInZone2()
                # self.updateGInZone()
            else:
                self.placeRandom()
                # self.updateG()

            # min_from_center = np.argmin([np.square(x.getCurLoc().getCol() - self.region_center_x) +
            #                       np.square(x.getCurLoc().getRow() - self.region_center_y) for x in self.patrols])
            # print("Min distance from region center is %i" % min_from_center)

        return

    # def updateGInZone(self):
    #     for p in self.patrols:
    #         d_p = self.findSegmentsInZone(p)
    #         p.initG(d_p.shape[0])
    #         for d in d_p:
    #             d_s = self.findSurroundingInZone(p, d["row"], d["col"])
    #             for dd in d_s:
    #                 u = p.getWTd() * (1 - dd["obj"].getTd()) + p.getWOb() * dd["obj"].getOb() + \
    #                     p.getWSt() * dd["obj"].getSt() / self.accu_tres
    #                 p.setG(d["row"]*d["col"]-1, dd["row"]*d["col"]-1, u)
    #
    # def updateG(self):
    #     for p in self.patrols:
    #         p.initG(self.number_row*self.number_col)
    #         for d in self.segments:
    #             d_s = self.findSurrounding(d["row"], d["col"])
    #             for dd in d_s:
    #                 u = p.getWTd() * (1 - dd["obj"].getTd()) + p.getWOb() * dd["obj"].getOb() + \
    #                     p.getWSt() * dd["obj"].getSt() / self.accu_tres
    #                 p.setG(d["row"]*d["col"]-1, dd["row"]*d["col"]-1, u)

    def placeRandom(self):
        bar_alpha = [d for d in self.segments if d["obj"].getTd() < 1]
        proximity_guard = int(np.ceil(self.number_row * 0.1))
        for p in range(self.num_patrol):
            d_p = np.random.choice(bar_alpha)
            s_p = d_p["obj"]
            patrolagent = PatrolAgent("patrol_" + str(p + 1), s_p,
                                      self.pos_x + (int(s_p.getCol() - 1) * self.grid_width),
                                      self.pos_y + (int(s_p.getRow()) - 1) * self.grid_width,
                                      self.grid_width, self.grid_width)
            self.patrols.append(patrolagent)
            self.scene.addItem(patrolagent)
            for r in range(int(s_p.getRow()) - proximity_guard, int(s_p.getRow()) + proximity_guard):
                for c in range(int(s_p.getCol()) - proximity_guard, int(s_p.getCol()) + proximity_guard):
                    tilde_alpha = [d for d in bar_alpha if d["row"] == r and d["col"] == c]
                    for e in tilde_alpha:
                        if e in bar_alpha:
                            bar_alpha.remove(e)
                        # bar_alpha[:] = [item for i, item in enumerate(bar_alpha) if i not in tilde_alpha]

    def placeOnMiddleLine(self):
        middle_col = int(self.number_col / 2) + 1
        bar_alpha = [d for d in self.segments if d["obj"].getTd() < 1 and d["col"] == middle_col]
        for p in range(self.num_patrol):
            d_p = np.random.choice(bar_alpha)
            s_p = d_p["obj"]
            patrolagent = PatrolAgent("patrol_" + str(p + 1), s_p,
                                      self.pos_x + (int(s_p.getCol() - 1) * self.grid_width),
                                      self.pos_y + (int(s_p.getRow()) - 1) * self.grid_width,
                                      self.grid_width, self.grid_width)
            self.patrols.append(patrolagent)
            self.scene.addItem(patrolagent)

    def placeOnDoubleLines(self):
        a = divmod(int(np.ceil(self.number_col * 1 / 4)), 5)
        b = divmod(int(np.ceil(self.number_col * 3 / 4)), 5)
        first_col = a[0] * 5 + 1
        second_col = b[0] * 5 + 1
        bar_alpha = [d for d in self.segments if
                     d["obj"].getTd() < 1 and (d["col"] == first_col or d["col"] == second_col)]
        for p in range(self.num_patrol):
            d_p = np.random.choice(bar_alpha)
            s_p = d_p["obj"]
            patrolagent = PatrolAgent("patrol_" + str(p + 1), s_p,
                                      self.pos_x + (int(s_p.getCol() - 1) * self.grid_width),
                                      self.pos_y + (int(s_p.getRow()) - 1) * self.grid_width,
                                      self.grid_width, self.grid_width)
            self.patrols.append(patrolagent)
            self.scene.addItem(patrolagent)

    def placeInZone(self):
        accu_L = sum(d["obj"].getL() for d in self.segments)
        avgL_per_zone = accu_L / self.num_patrol
        print("Total L is %f" % accu_L)
        print("Avg. L per zone is %f" % avgL_per_zone)
        bar_alpha = [d for d in self.segments if d["obj"].getTd() < 1]
        expanded = []
        expanding = []
        nextexpand = []
        parents = []
        endnodes = []
        row = 1
        col = 1
        first_segment = None
        for r in range(self.number_row):
            d = self.findSegment(r + 1, 1)
            if d["obj"].getTd() < 1:
                first_segment = d
                break

        # first_segment = self.findSegment(row, col)
        parents.append(first_segment)
        for p in range(self.num_patrol - 1):
            red = np.random.randint(low=0, high=255)
            green = np.random.randint(low=0, high=255)
            blue = np.random.randint(low=0, high=255)
            alpha = 150
            accu_L_p = 0
            bar_alpha_p = []
            exp_node = np.random.choice(parents)
            expanding.append(exp_node)
            parents.remove(exp_node)
            while accu_L_p < avgL_per_zone:
                if not expanding and accu_L_p < avgL_per_zone:
                    exp_node = np.random.choice(parents)
                    expanding.append(exp_node)
                    parents.remove(exp_node)
                endnodes = []
                for e in expanding:
                    if e in bar_alpha:
                        s_e = e["obj"]
                        s_e.setZone("patrol_" + str(p + 1))
                        s_e.setBrush(QColor(red, green, blue, alpha))
                        accu_L_p = accu_L_p + s_e.getL()
                        bar_alpha_p.append(e)
                        expanded.append(e)
                        endnodes.append(e)
                        expanding.remove(e)
                    next_segments = self.findFreeSurrounding(e["row"], e["col"])
                    for e0 in expanded:
                        if e0 in next_segments:
                            next_segments.remove(e0)
                        # next_segments = [item for i, item in enumerate(next_segments) if i not in expanded]
                    for e0 in expanding:
                        if e0 in next_segments:
                            next_segments.remove(e0)
                        # next_segments = [item for i, item in enumerate(next_segments) if i not in expanding]
                    for e0 in nextexpand:
                        if e0 in next_segments:
                            next_segments.remove(e0)
                        # next_segments = [item for i, item in enumerate(next_segments) if i not in nextexpand]
                    nextexpand.extend(next_segments)

                expanding = []
                expanding.extend(nextexpand)
                nextexpand = []
            parents.extend(expanding)
            expanding = []
            # s_in_z = [d for d in self.segments if d["obj"].getZone() == "patrol_" + str(p + 1)]
            # no_neighbor_nodes = [n for n in s_in_z if not self.findSurroundingInZone2("patrol_" + str(p + 1), n["obj"].getRow(), n["obj"].getCol())]
            for node in endnodes:
                g_ = [g for g in endnodes if g is not node and g["obj"].getRow() == node["obj"].getRow() and abs(
                    g["obj"].getCol() - node["obj"].getCol()) <= 4]
                h_ = [h for h in endnodes if h is not node and h["obj"].getCol() == node["obj"].getCol() and abs(
                    h["obj"].getRow() - node["obj"].getRow()) <= 9]
                if node["obj"].getRow() <= 11 and (node["obj"].getCol() % 5) == 1:
                    for i in range(1, node["obj"].getRow()):
                        d = self.findSegment(i, node["obj"].getCol())
                        if d in parents:
                            parents.remove(d)
                        s = d["obj"]
                        s.setZone("patrol_" + str(p + 1))
                        s.setBrush(QColor(red, green, blue, alpha))
                    endnodes.remove(node)
                elif node["obj"].getRow() >= 91 and (node["obj"].getCol() % 5) == 1:
                    for i in range(node["obj"].getRow() + 1, 101):
                        d = self.findSegment(i, node["obj"].getCol())
                        if d in parents:
                            parents.remove(d)
                        s = d["obj"]
                        s.setZone("patrol_" + str(p + 1))
                        s.setBrush(QColor(red, green, blue, alpha))
                    endnodes.remove(node)
                elif node["obj"].getCol() <= 6 and (node["obj"].getRow() % 10) == 1:
                    for i in range(1, node["obj"].getCol()):
                        d = self.findSegment(node["obj"].getRow(), i)
                        if d in parents:
                            parents.remove(d)
                        s = d["obj"]
                        s.setZone("patrol_" + str(p + 1))
                        s.setBrush(QColor(red, green, blue, alpha))
                    endnodes.remove(node)
                elif node["obj"].getCol() >= 46 and (node["obj"].getRow() % 10) == 1:
                    for i in range(node["obj"].getCol() + 1, 51):
                        d = self.findSegment(node["obj"].getRow(), i)
                        if d in parents:
                            parents.remove(d)
                        s = d["obj"]
                        s.setZone("patrol_" + str(p + 1))
                        s.setBrush(QColor(red, green, blue, alpha))
                    endnodes.remove(node)
            #     elif g_:
            #         for g in g_:
            #             if g["obj"].getCol() > node["obj"].getCol():
            #                 for i in range(node["obj"].getCol()+1, g["obj"].getCol()):
            #                     d = self.findSegment(node["obj"].getRow(), i)
            #                     s = d["obj"]
            #                     s.setZone("patrol_" + str(p + 1))
            #                     s.setBrush(QColor(red, green, blue, alpha))
            #             else:
            #                 for i in range(g["obj"].getCol()+1, node["obj"].getCol()):
            #                     d = self.findSegment(node["obj"].getRow(), i)
            #                     s = d["obj"]
            #                     s.setZone("patrol_" + str(p + 1))
            #                     s.setBrush(QColor(red, green, blue, alpha))
            #             parents.remove(g)
            #         parents.remove(node)
            #     elif h_:
            #         for h in h_:
            #             if h["obj"].getRow() > node["obj"].getRow():
            #                 for i in range(node["obj"].getRow()+1, h["obj"].getRow()):
            #                     d = self.findSegment(i, node["obj"].getCol())
            #                     s = d["obj"]
            #                     s.setZone("patrol_" + str(p + 1))
            #                     s.setBrush(QColor(red, green, blue, alpha))
            #             else:
            #                 for i in range(h["obj"].getRow()+1, node["obj"].getRow()):
            #                     d = self.findSegment(i, node["obj"].getCol())
            #                     s = d["obj"]
            #                     s.setZone("patrol_" + str(p + 1))
            #                     s.setBrush(QColor(red, green, blue, alpha))
            #             parents.remove(h)
            #         parents.remove(node)

            d_p = np.random.choice(bar_alpha_p)
            s_p = d_p["obj"]
            patrolagent = PatrolAgent("patrol_" + str(p + 1), s_p,
                                      self.pos_x + (int(s_p.getCol() - 1) * self.grid_width),
                                      self.pos_y + (int(s_p.getRow()) - 1) * self.grid_width,
                                      self.grid_width, self.grid_width)
            self.patrols.append(patrolagent)
            self.scene.addItem(patrolagent)
            for e1 in bar_alpha_p:
                if e1 in bar_alpha:
                    bar_alpha.remove(e1)

        for e in bar_alpha:
            s_e = e["obj"]
            s_e.setZone("patrol_" + str(self.num_patrol))

        d_p = np.random.choice(bar_alpha)
        s_p = d_p["obj"]
        patrolagent = PatrolAgent("patrol_" + str(self.num_patrol), s_p,
                                  self.pos_x + (int(s_p.getCol() - 1) * self.grid_width),
                                  self.pos_y + (int(s_p.getRow()) - 1) * self.grid_width,
                                  self.grid_width, self.grid_width)
        self.patrols.append(patrolagent)
        self.scene.addItem(patrolagent)

    def placeInZone2(self):
        for d in self.segments:
            if d["obj"].getZone():
                d["obj"].setZone(None)
                d["obj"].setBrush(QColor(0, 0, 0, 0))

        accu_L = sum(d["obj"].getL() for d in self.segments)
        avgL_per_zone = accu_L / self.num_patrol
        print("Total L is %f" % accu_L)
        print("Avg. L per zone is %f" % avgL_per_zone)
        bar_alpha = [d for d in self.segments if d["obj"].getTd() < 1]

        for p in range(self.num_patrol):
            red = np.random.randint(low=0, high=255)
            green = np.random.randint(low=0, high=255)
            blue = np.random.randint(low=0, high=255)
            alpha = 150
            accu_L_p = 0
            bar_alpha_p = []
            expanding = []
            expanded = []
            endnodes = []
            nextexpand = []
            exp_node = np.random.choice(bar_alpha)
            expanding.append(exp_node)
            while accu_L_p < avgL_per_zone*self.zoning_scale:
                if not expanding and accu_L_p > avgL_per_zone*self.zoning_scale*0.8:
                    # exp_node = np.random.choice(bar_alpha)
                    # expanding.append(exp_node)
                    break
                elif not expanding:
                    exp_node = np.random.choice(bar_alpha)
                    expanding.append(exp_node)
                    for d in bar_alpha_p:
                        d["obj"].setZone(None)
                        d["obj"].setBrush(QColor(0, 0, 0, 0))
                    bar_alpha_p = []
                # endnodes = []
                for e in expanding:
                    if e in bar_alpha:
                        s_e = e["obj"]
                        s_e.setZone("patrol_" + str(p + 1))
                        s_e.setBrush(QColor(red, green, blue, alpha))
                        accu_L_p = accu_L_p + s_e.getL()
                        bar_alpha_p.append(e)
                        bar_alpha.remove(e)
                        expanded.append(e)
                        # endnodes.append(e)
                        # expanding.remove(e)
                        if accu_L_p >= avgL_per_zone*0.8:
                            break
                        next_segments = self.findFreeSurrounding(e["row"], e["col"])
                        for e0 in expanded:
                            if e0 in next_segments:
                                next_segments.remove(e0)
                            # next_segments = [item for i, item in enumerate(next_segments) if i not in expanded]
                        for e0 in expanding:
                            if e0 in next_segments:
                                next_segments.remove(e0)
                            # next_segments = [item for i, item in enumerate(next_segments) if i not in expanding]
                        for e0 in nextexpand:
                            if e0 in next_segments:
                                next_segments.remove(e0)
                            # next_segments = [item for i, item in enumerate(next_segments) if i not in nextexpand]
                        if next_segments:
                            # endnodes.remove(e)
                            nextexpand.extend(next_segments)

                expanding = []
                expanding.extend(nextexpand)
                nextexpand = []

            expanding = []
            endnodes = []
            for d in bar_alpha_p:
                if ((1 < d["obj"].getRow() < 6) or (96 < d["obj"].getRow() < 100) or
                        (1 < d["obj"].getCol() < 6) or (46 < d["obj"].getCol() < 50)):
                    d_ = self.findSurroundingInZone2("patrol_" + str(p + 1), d["obj"].getRow(), d["obj"].getCol())
                    if len(d_) <=1 or (d["obj"].getCol() == 5 and self.findSegment(d["obj"].getRow(), 4)["obj"].getZone() is None) or \
                            (d["obj"].getCol() == 47 and self.findSegment(d["obj"].getRow(), 48)["obj"].getZone() is None) or \
                            (d["obj"].getRow() == 5 and self.findSegment(4, d["obj"].getCol())["obj"].getZone() is None) or \
                            (d["obj"].getRow() == 97 and self.findSegment(98, d["obj"].getCol())["obj"].getZone() is None):
                        endnodes.append(d)


            # s_in_z = [d for d in self.segments if d["obj"].getZone() == "patrol_" + str(p + 1)]
            # no_neighbor_nodes = [n for n in s_in_z if not self.findSurroundingInZone2("patrol_" + str(p + 1), n["obj"].getRow(), n["obj"].getCol())]
            for node in endnodes:
                if node["obj"].getRow() < 6 and (node["obj"].getCol() % 5) == 1:
                    for i in range(1, node["obj"].getRow()):
                        d = self.findSegment(i, node["obj"].getCol())
                        s = d["obj"]
                        s.setZone("patrol_" + str(p + 1))
                        bar_alpha_p.append(d)
                        bar_alpha.remove(d)
                        s.setBrush(QColor(red, green, blue, alpha))
                    # endnodes.remove(node)
                elif node["obj"].getRow() > 96 and (node["obj"].getCol() % 5) == 1:
                    for i in range(node["obj"].getRow() + 1, 101):
                        d = self.findSegment(i, node["obj"].getCol())
                        s = d["obj"]
                        s.setZone("patrol_" + str(p + 1))
                        bar_alpha_p.append(d)
                        bar_alpha.remove(d)
                        s.setBrush(QColor(red, green, blue, alpha))
                    # endnodes.remove(node)
                elif node["obj"].getCol() < 6 and (node["obj"].getRow() % 5) == 1:
                    for i in range(1, node["obj"].getCol()):
                        d = self.findSegment(node["obj"].getRow(), i)
                        s = d["obj"]
                        s.setZone("patrol_" + str(p + 1))
                        bar_alpha_p.append(d)
                        bar_alpha.remove(d)
                        s.setBrush(QColor(red, green, blue, alpha))
                    # endnodes.remove(node)
                elif node["obj"].getCol() > 46 and (node["obj"].getRow() % 5) == 1:
                    for i in range(node["obj"].getCol() + 1, 51):
                        d = self.findSegment(node["obj"].getRow(), i)
                        s = d["obj"]
                        s.setZone("patrol_" + str(p + 1))
                        bar_alpha_p.append(d)
                        bar_alpha.remove(d)
                        s.setBrush(QColor(red, green, blue, alpha))
                    # endnodes.remove(node)
            #     elif g_:
            #         for g in g_:
            #             if g["obj"].getCol() > node["obj"].getCol():
            #                 for i in range(node["obj"].getCol()+1, g["obj"].getCol()):
            #                     d = self.findSegment(node["obj"].getRow(), i)
            #                     s = d["obj"]
            #                     s.setZone("patrol_" + str(p + 1))
            #                     s.setBrush(QColor(red, green, blue, alpha))
            #             else:
            #                 for i in range(g["obj"].getCol()+1, node["obj"].getCol()):
            #                     d = self.findSegment(node["obj"].getRow(), i)
            #                     s = d["obj"]
            #                     s.setZone("patrol_" + str(p + 1))
            #                     s.setBrush(QColor(red, green, blue, alpha))
            #             parents.remove(g)
            #         parents.remove(node)
            #     elif h_:
            #         for h in h_:
            #             if h["obj"].getRow() > node["obj"].getRow():
            #                 for i in range(node["obj"].getRow()+1, h["obj"].getRow()):
            #                     d = self.findSegment(i, node["obj"].getCol())
            #                     s = d["obj"]
            #                     s.setZone("patrol_" + str(p + 1))
            #                     s.setBrush(QColor(red, green, blue, alpha))
            #             else:
            #                 for i in range(h["obj"].getRow()+1, node["obj"].getRow()):
            #                     d = self.findSegment(i, node["obj"].getCol())
            #                     s = d["obj"]
            #                     s.setZone("patrol_" + str(p + 1))
            #                     s.setBrush(QColor(red, green, blue, alpha))
            #             parents.remove(h)
            #         parents.remove(node)

            d_p = np.random.choice(bar_alpha_p)
            s_p = d_p["obj"]
            patrolagent = PatrolAgent("patrol_" + str(p + 1), s_p,
                                      self.pos_x + (int(s_p.getCol() - 1) * self.grid_width),
                                      self.pos_y + (int(s_p.getRow()) - 1) * self.grid_width,
                                      self.grid_width, self.grid_width)
            self.patrols.append(patrolagent)
            self.scene.addItem(patrolagent)
            # for e1 in bar_alpha_p:
            #     if e1 in bar_alpha:
            #         bar_alpha.remove(e1)

        # for e in bar_alpha:
        #     s_e = e["obj"]
        #     s_e.setZone("patrol_" + str(self.num_patrol))

        # d_p = np.random.choice(bar_alpha)
        # s_p = d_p["obj"]
        # patrolagent = PatrolAgent("patrol_" + str(self.num_patrol), s_p,
        #                           self.pos_x + (int(s_p.getCol() - 1) * self.grid_width),
        #                           self.pos_y + (int(s_p.getRow()) - 1) * self.grid_width,
        #                           self.grid_width, self.grid_width)
        # self.patrols.append(patrolagent)
        # self.scene.addItem(patrolagent)

    def findSegment(self, i, j):
        value = [d for d in self.segments if d["row"] == i and d["col"] == j]
        # value = filter(lambda s: s[0] == key, self.segments["segments"])
        # print(len(value))
        if len(value) > 0:
            return value[0]
        else:
            return None

    def findSurrounding(self, i, j):
        return [d for d in self.segments if
                ((d["row"] == i - 1 and d["col"] == j - 1) or (d["row"] == i - 1 and d["col"] == j)
                 or (d["row"] == i - 1 and d["col"] == j + 1) or (d["row"] == i and d["col"] == j + 1)
                 or (d["row"] == i + 1 and d["col"] == j + 1) or (d["row"] == i + 1 and d["col"] == j)
                 or (d["row"] == i + 1 and d["col"] == j - 1) or (d["row"] == i and d["col"] == j - 1))
                and d["obj"].getTd() < 1]
        # return [d for d in self.segments if
        #         (i - 1 <= d["row"] <= i + 1 and j - 1 <= d["col"] <= j + 1)
        #         and d["obj"].getTd() < 1]

    def findFreeSurrounding(self, i, j):
        # return [d for d in self.segments if
        #         ((d["row"] == i - 1 and d["col"] == j - 1) or (d["row"] == i - 1 and d["col"] == j)
        #          or (d["row"] == i - 1 and d["col"] == j + 1) or (d["row"] == i and d["col"] == j + 1)
        #          or (d["row"] == i + 1 and d["col"] == j + 1) or (d["row"] == i + 1 and d["col"] == j)
        #          or (d["row"] == i + 1 and d["col"] == j - 1) or (d["row"] == i and d["col"] == j - 1))
        #         and d["obj"].getTd() < 1]
        return [d for d in self.segments if
                (i - 1 <= d["row"] <= i + 1 and j - 1 <= d["col"] <= j + 1) and 5 < d["row"] < 97
                and d["obj"].getTd() < 1 and d["obj"].getZone() is None]

    def findUpDownSegments(self, i, j):
        return [d for d in self.segments if
                ((d["row"] == i - 1 and d["col"] == j) or (d["row"] == i + 1 and d["col"] == j))
                and d["obj"].getTd() < 1]

    def findUpSegment(self, i, j):
        return [d for d in self.segments if d["row"] == i + 1 and d["col"] == j and d["obj"].getTd() < 1]

    def findDownSegment(self, i, j):
        return [d for d in self.segments if d["row"] == i - 1 and d["col"] == j and d["obj"].getTd() < 1]

    def findSegmentsInZone(self, p):
        return [d for d in self.segments if d["obj"].getZone == p.getId()]

    def findSurroundingInZone(self, p, i, j):
        return [d for d in self.segments if
                ((d["row"] == i - 1 and d["col"] == j - 1) or (d["row"] == i - 1 and d["col"] == j)
                 or (d["row"] == i - 1 and d["col"] == j + 1) or (d["row"] == i and d["col"] == j + 1)
                 or (d["row"] == i + 1 and d["col"] == j + 1) or (d["row"] == i + 1 and d["col"] == j)
                 or (d["row"] == i + 1 and d["col"] == j - 1) or (d["row"] == i and d["col"] == j - 1))
                and d["obj"].getTd() < 1 and d["obj"].getZone() == p.getId()]
        # return [d for d in self.segments if
        #         (i - 1 <= d["row"] <= i + 1 and j - 1 <= d["col"] <= j + 1)
        #         and d["obj"].getTd() < 1 and d["obj"].getZone() == p.getId()]

    def findSurroundingInZone2(self, pid, i, j):
        return [d for d in self.segments if
                ((d["row"] == i - 1 and d["col"] == j - 1) or (d["row"] == i - 1 and d["col"] == j)
                 or (d["row"] == i - 1 and d["col"] == j + 1) or (d["row"] == i and d["col"] == j + 1)
                 or (d["row"] == i + 1 and d["col"] == j + 1) or (d["row"] == i + 1 and d["col"] == j)
                 or (d["row"] == i + 1 and d["col"] == j - 1) or (d["row"] == i and d["col"] == j - 1))
                and d["obj"].getTd() < 1 and d["obj"].getZone() == pid]
        # return [d for d in self.segments if
        #         (i - 1 <= d["row"] <= i + 1 and j - 1 <= d["col"] <= j + 1)
        #         and d["obj"].getTd() < 1 and d["obj"].getZone() == pid]

    def findSegmentsInCoverage(self, i, j, r):
        return [d for d in self.segments if
                (i - r <= d["row"] <= i + r and j - r <= d["col"] <= j + r)
                and d["obj"].getTd() < 1]

    def startSim(self):
        # for s in self.patrollers:
        #     startA = s.getStartLoc()
        #     s.setCurrentLoc(startA)
        #     s_node = s.getNode()
        #     s_node.setPos(0, 0)
        self.pauseButton.setDisabled(False)
        self.resumeButton.setDisabled(True)
        self.resetButton.setDisabled(False)
        self.stopButton.setDisabled(False)
        self.runButton.setDisabled(True)
        self.resetSim()

    def resumeSim(self):
        self.pauseButton.setDisabled(False)
        self.resumeButton.setDisabled(True)
        self.timer.start(self.stage_duration * 1000)

    def pauseSim(self):
        self.pauseButton.setDisabled(True)
        self.resumeButton.setDisabled(False)
        self.display_sim_status_val.setPlainText("Paused")
        self.timer.stop()

    def resetSim(self):
        self.timer.stop()

        self.curP = 1
        self.curT = 0
        self.number_t_entry = 0
        self.number_t_exit = 0
        self.number_t_detected = 0
        self.resetLoc()
        self.initResult1Table()
        self.result1_df = pd.DataFrame(columns=['entering', 'leaving', 'detected', 'detection_rate'])
        self.display_cur_period_val.setPlainText(str(self.curP))
        self.display_cur_stage_val.setPlainText(str(self.curT))
        self.display_sim_status_val.setPlainText("Stopped")
        # for t in self.trespassers:
        #     if t.getStatus() == 1:
        #         self.scene.removeItem(t)
        #
        # for p in self.patrols:
        #     s_init = p.getInitLoc()
        #     p.setPos(self.pos_x + (int(s_init.getCol() - 1) * self.grid_width),
        #              self.pos_y + (int(s_init.getRow()) - 1) * self.grid_width)
        #     p.resetObservation()
        #     p.resetFoundTrespasser()
        #     p.setPOMDPStatus(False)
        #
        # self.trespassers = []
        self.avgResult1.setText(str(0))
        self.display_sim_status_val.setPlainText("Running")
        self.timer.start(self.stage_duration * 1000)

    def stopSim(self):
        self.pauseButton.setDisabled(True)
        self.resumeButton.setDisabled(True)
        self.resetButton.setDisabled(True)
        self.stopButton.setDisabled(True)
        self.runButton.setDisabled(False)
        self.curP = 1
        self.curT = 0
        self.number_t_entry = 0
        self.number_t_exit = 0
        self.number_t_detected = 0
        self.display_sim_status_val.setPlainText("Stopped")
        # for t in self.trespassers:
        #     if t.getStatus() == 1:
        #         self.scene.removeItem(t)

        # for p in self.patrols:
        #     s_init = p.getInitLoc()
        #     p.setPos(self.pos_x + (int(s_init.getCol() - 1) * self.grid_width),
        #              self.pos_y + (int(s_init.getRow()) - 1) * self.grid_width)
        #     p.resetObservation()
        #     p.resetFoundTrespasser()
        #     p.setPOMDPStatus(False)

        # self.trespassers = []
        self.timer.stop()
        return
        # self.timer.stop()

    def resetLoc(self):
        for l in self.patrols:
            s_cur = l.getCurLoc()
            l_point = s_cur.pos()
            s_init = l.getInitLoc()
            l.setPos(l_point.x() + (s_init.getCol() - s_cur.getCol()) * self.grid_width,
                     l_point.y() + (s_init.getRow() - s_cur.getRow()) * self.grid_width)

    def initResult1Table(self):
        self.result1Tbl.clearContents()

        for rnd in range(self.num_period):
            self.result1Tbl.insertRow(self.result1Tbl.rowCount())
            item0 = QTableWidgetItem()
            item0.setData(Qt.DisplayRole, rnd + 1)
            item1 = QTableWidgetItem()
            item1.setData(Qt.DisplayRole, 0)
            item2 = QTableWidgetItem()
            item2.setData(Qt.DisplayRole, 0)
            item3 = QTableWidgetItem()
            item3.setData(Qt.DisplayRole, 0)
            item4 = QTableWidgetItem()
            item4.setData(Qt.DisplayRole, 0)
            self.result1Tbl.setItem(rnd, 0, item0)
            self.result1Tbl.setItem(rnd, 1, item1)
            self.result1Tbl.setItem(rnd, 2, item2)
            self.result1Tbl.setItem(rnd, 3, item3)
            self.result1Tbl.setItem(rnd, 4, item4)

    def simulate(self):
        if self.curT > self.period_len:
            self.curT = 0
            self.curP = self.curP + 1
            detection_rate = 0
            if self.number_t_exit + self.number_t_detected > 0:
                detection_rate = float(self.number_t_detected / (self.number_t_exit + self.number_t_detected))
                item = QTableWidgetItem()
                item.setData(Qt.DisplayRole,
                             float(self.number_t_detected / (self.number_t_exit + self.number_t_detected)))
                self.detection_rate_per_round.append(
                    float(self.number_t_detected / (self.number_t_exit + self.number_t_detected)))
            else:
                detection_rate = 0
                item = QTableWidgetItem()
                item.setData(Qt.DisplayRole, 0)
                self.detection_rate_per_round.append(0)

            self.result1Tbl.setItem(self.curP - 2, 4, item)
            data_series = pd.Series([
                self.number_t_entry,
                self.number_t_exit,
                self.number_t_detected,
                detection_rate
            ], index=[
                'entering',
                'leaving',
                'detected',
                'detection_rate'
            ])
            self.result1_df = self.result1_df.append(data_series, ignore_index=True)
            self.number_t_entry = 0
            self.number_t_exit = 0
            self.number_t_detected = 0
        if self.curP > self.num_period:
            self.avg_tres_detection_rate = self.result1_df['detection_rate'].mean()
            self.avgResult1.setText(str(self.avg_tres_detection_rate))
            self.stopSim()
            return

        self.display_cur_period_val.setPlainText(str(self.curP))
        self.display_cur_stage_val.setPlainText(str(self.curT))

        if self.curT == 0:
            for p in self.patrols:
                p.resetObservation()
                p.resetFoundTrespasser()
                p.setPOMDPStatus(False)
            for k in self.trespassers:
                self.scene.removeItem(k)
            self.generateTrespassers()
            self.generateNoise()
            self.generatePatrolPlan()
            # reset footprint value in every segment
            self.resetFootprintVal()

        # increase footprint value in a segment that has been trespassed or patrolled
        for d in self.segments:
            if not np.isinf(d["obj"].getTFp()):
                d["obj"].setTFp(d["obj"].getTFp() + 1)
            if not np.isinf(d["obj"].getPFp()):
                d["obj"].setPFp(d["obj"].getPFp() + 1)
        # move trespasser
        # if len(self.trespassers) > 0:
        #     with parallel_backend('threading', n_jobs=len(self.trespassers)):
        #         Parallel()(delayed(self.moveOneTrespasser)(i) for i in self.trespassers)
        for i in self.trespassers:
            self.moveOneTrespasser(i)

        # if len(self.noises) > 0:
        #     with parallel_backend('threading', n_jobs=len(self.noises)):
        #         Parallel()(delayed(self.moveOneNoise)(i) for i in self.noises)
        for i in self.noises:
            self.moveOneNoise(i)

        self.trespasser_found = False
        # move patrol
        # with parallel_backend('threading', n_jobs=self.num_patrol):
        #     Parallel()(delayed(self.patrolProcess)(i) for i in self.patrols)
        for i in self.patrols:
            self.patrolProcess(i)

        # with parallel_backend('threading', n_jobs=self.num_patrol):
        #     Parallel()(delayed(self.detectionProcess)(i) for i in self.patrols)

        # if self.trespasser_move_model == 2:
        #     for k in self.trespassers:
        #         if (not np.isinf(k.getCurLoc().getPFp())) and k.getStatus() == 1:
        #             # take the footprint with the prob equal to observing confidence
        #             fp_d = np.random.choice([0, 1], p=[1 - k.getObservingConfidence(), k.getObservingConfidence()])
        #             if fp_d == 1:
        #                 # construct belief
        #                 d_b = self.findSegmentsInCoverage(k.getCurLoc().getRow(), k.getCurLoc().getCol(),
        #                                                   k.getCurLoc().getPFp())
        #                 k.resetBelief()
        #                 for dd_b in d_b:
        #                     k.addToBelief(dd_b["obj"])
        #                 self.findTrespasserPathWithFP(k, k.getCurLoc(), k.getDestination())

        if self.patrol_move_model == 4:
            # collect footprints
            for l in self.patrols:
                if not np.isinf(l.getCurLoc().getTFp()):
                    l.addObservation(self.curT, l.getId(),
                                     (l.getCurLoc().getRow(), l.getCurLoc().getCol(), l.getCurLoc().getTFp()))
                else:
                    l.addObservation(self.curT, l.getId(), None)
                for m in [n for n in self.patrols if n != l]:
                    comm_result = np.random.choice([0, 1], p=[1 - self.comm_success_rate, self.comm_success_rate])
                    confd = np.random.choice([0, 1], p=[1 - m.getObservingConfidence(), m.getObservingConfidence()])
                    if not np.isinf(m.getCurLoc().getTFp()) and comm_result == 1 and confd == 1:
                        l.addObservation(self.curT, m.getId(),
                                         (m.getCurLoc().getRow(), m.getCurLoc().getCol(), m.getCurLoc().getTFp()))
                    else:
                        l.addObservation(self.curT, m.getId(), None)

            # utilize observed footprints
            for l in self.patrols:
                if l.getStatus() == 1:
                    l.resetBelief()
                    # if has never found footprint before, activate POMDP
                    if not l.getPOMDPStatus() and l.getObservationHistory():
                        cur_fp = [(m, l.getObservationAt(self.curT, m)) for m in self.patrols if
                                  l.getObservationAt(self.curT, m) is not None]
                        for fp in cur_fp:
                            mm = fp[0]
                            fpp = fp[1]
                            d_b = self.findSegmentsInCoverage(mm.getCurLoc().getRow(), mm.getCurLoc().getCol(),
                                                              fpp[2])
                            for dd_b in d_b:
                                l.addToBelief(dd_b["obj"])
                        # call POMDP plan for action in the next time stage
                        if l.getBelief():
                            l.setPOMDPStatus(True)
                            self.POMDPPlanning(l)
                        elif l.getReplanStage() == self.curT:
                            self.heuristicPath(l, self.curT)
                    # else if POMDP is active
                    elif l.getPOMDPStatus():
                        cur_fp = [(m, l.getObservationAt(self.curT, m)) for m in self.patrols if
                                  l.getObservationAt(self.curT, m) is not None]
                        cur_none_fp = [(m, l.getObservationAt(self.curT, m)) for m in self.patrols if
                                       l.getObservationAt(self.curT, m) is None]
                        for fp in cur_fp:
                            mm = fp[0]
                            fpp = fp[1]
                            d_b = self.findSegmentsInCoverage(mm.getCurLoc().getRow(), mm.getCurLoc().getCol(),
                                                              fpp[2])
                            for dd_b in d_b:
                                l.addToBelief(dd_b["obj"])
                        for n_fp in cur_none_fp:
                            mm = n_fp[0]
                            l_history = l.getObservationHistory()
                            past_fp_stages = [k[0] for k in l_history.keys() if
                                              (l_history[k] is not None) and k[1] == mm]
                            if past_fp_stages:
                                last_fp_stage = max(past_fp_stages)
                                nfp_interval = self.curT - last_fp_stage
                                if nfp_interval < self.allowed_no_fp_stages:
                                    fpp = l.getObservationAt(last_fp_stage, mm)
                                    d_b = self.findSegmentsInCoverage(fpp[0], fpp[1], fpp[2] + nfp_interval)
                                    for dd_b in d_b:
                                        l.addToBelief(dd_b["obj"])

                        if l.getBelief():
                            l.setPOMDPStatus(True)
                            self.POMDPPlanning(l)
                        else:
                            l.setPOMDPStatus(False)
                            self.heuristicPath(l, self.curT)

        else:
            # with parallel_backend('threading', n_jobs=self.num_patrol):
            #     Parallel()(delayed(self.rePlanningProcess)(i) for i in self.patrols)
            for i in self.patrols:
                self.rePlanningProcess(i)

        # if self.trespasser_found and (self.patrol_move_model == 3 or self.patrol_move_model == 4):
        #     # update patrol path
        #     for l in self.patrols:
        #         comm_result = np.random.choice([0,1], p=[1-self.comm_success_rate, self.comm_success_rate])
        #         if not l.getPOMDPStatus() and comm_result == 1:
        #             self.heuristicPath(l, self.curT)

        self.curT = self.curT + 1

    def moveOneTrespasser(self, k):
        if k.getArrTime() == self.curT and k.getStatus() == 0:
            s_cur = k.getInitLoc()
            s_cur.setTFp(0)
            s_cur.setLastTrespassedBy(k)
            k.setStatus(1)
            self.scene.addItem(k)
            self.number_t_entry = self.number_t_entry + 1
            item = QTableWidgetItem()
            item.setData(Qt.DisplayRole, self.number_t_entry)
            self.result1Tbl.setItem(self.curP - 1, 1, item)

        elif k.getArrTime() < self.curT and k.getStatus() == 1 and k.getCurLoc().getCol() != self.number_col:
            k_point = k.pos()
            s_cur = k.getCurLoc()
            if s_cur not in k.getTrespassed():
                k.addTrespassed(s_cur)
            # s_cur.setFp(s_cur.getTFp() + 1)
            if k.getMoveModel() != 0:
                s = k.getSegmentFromPlan(self.curT)
                k.setPos(k_point.x() + (s.getCol() - s_cur.getCol()) * self.grid_width,
                         k_point.y() + (s.getRow() - s_cur.getRow()) * self.grid_width)
                k.setCurLoc(s)
                k.setPrevLoc(s_cur)
                s.setTFp(0)
                s.setLastTrespassedBy(k)
            else:
                surroundings = self.findSurrounding(s_cur.getRow(), s_cur.getCol())
                p_sur = []
                for sur in surroundings:
                    if sur["obj"].getCol() > s_cur.getCol():
                        p_sur.append(0.3)
                    elif sur["obj"].getCol() == s_cur.getCol():
                        p_sur.append(0.2)
                    else:
                        p_sur.append(0.1)
                p_sur_ = [p_ / sum(p_sur) for p_ in p_sur]
                d_random = np.random.choice(surroundings, p=p_sur_)
                s_random = d_random["obj"]
                k.setPos(k_point.x() + (s_random.getCol() - s_cur.getCol()) * self.grid_width,
                         k_point.y() + (s_random.getRow() - s_cur.getRow()) * self.grid_width)
                k.setCurLoc(s_random)
                k.setPrevLoc(s_cur)
                s_random.setTFp(0)
                s_random.setLastTrespassedBy(k)

        elif k.getCurLoc().getCol() == self.number_col and k.getStatus() == 1:
            s_cur = k.getCurLoc()
            if s_cur not in k.getTrespassed():
                k.addTrespassed(s_cur)
            k.setStatus(3)
            self.scene.removeItem(k)
            self.number_t_exit = self.number_t_exit + 1
            item = QTableWidgetItem()
            item.setData(Qt.DisplayRole, self.number_t_exit)
            self.result1Tbl.setItem(self.curP - 1, 2, item)

    def moveOneNoise(self, noise):
        if noise.getArrTime() == self.curT and noise.getStatus() == 0:
            s_cur = noise.getInitLoc()
            noise.setStatus(1)
            self.scene.addItem(noise)
        elif noise.getArrTime() < self.curT and noise.getStatus() == 1 and \
                (noise.getCurLoc().getCol() != self.number_col and noise.getCurLoc().getCol() != 1 and
                 noise.getCurLoc().getRow() != self.number_row and noise.getCurLoc().getRow() != 1):
            n_point = noise.pos()
            s_cur = noise.getCurLoc()
            # s_cur.setFp(s_cur.getTFp() + 1)

            surroundings = self.findSurrounding(s_cur.getRow(), s_cur.getCol())
            d_random = np.random.choice(surroundings)
            s_random = d_random["obj"]
            noise.setPos(n_point.x() + (s_random.getCol() - s_cur.getCol()) * self.grid_width,
                         n_point.y() + (s_random.getRow() - s_cur.getRow()) * self.grid_width)
            noise.setCurLoc(s_random)
            noise.setPrevLoc(s_cur)
        elif noise.getStatus() == 1 and \
                (noise.getCurLoc().getCol() == self.number_col or noise.getCurLoc().getCol() == 1 or
                 noise.getCurLoc().getRow() == self.number_row or noise.getCurLoc().getRow() == 1):
            s_cur = noise.getCurLoc()
            noise.setStatus(3)
            self.scene.removeItem(noise)

    def patrolProcess(self, l):
        if self.curT == 0:
            s_cur = l.getCurLoc()
            s_cur.setPFp(0)
            s_cur.setLastPatrolledBy(l)
            s_cur.setLastPatrolledAt(self.curT)
            # l.setPos(0, 0)
            l.setStatus(1)
            ss = l.getFPSensor()
            if ss:
                ss.setLoc(s_cur)
            # self.detectionProcess(l)
        elif self.curT >= 1 and l.getStatus() == 2:
            s = l.getSegmentFromPlan(self.curT)
            l.setCurLoc(s)
            l.setPrevLoc(None)
            s.setPFp(0)
            s.setLastPatrolledBy(l)
            s.setLastPatrolledAt(self.curT)
            ss = l.getFPSensor()
            if ss:
                ss.setLoc(s)
            if l.getInvestigatingTime() < (self.investigation_time - 1):
                print("***investigating****")
                l.incrementInvestigatingTime()
            else:
                print("***finish investigating****")
                l.setStatus(1)
                l.resetInvestigatingTime()
                # update statistic in trespassed segments if detected entity is trespasser
                if l.getInvestigatedEntity().isTarget:
                    self.accu_tres = self.accu_tres + 1
                    for s_tres in l.getInvestigatedEntity().getTrespassed():
                        print("Update stat at %s" % s_tres.getId())
                        s_tres.setSt(s_tres.getSt() + 1)
                        s_tres.calScore(self.accu_tres)
                    # report trespasser found
                    self.trespasser_found = True
                    founded_tres = l.getInvestigatedEntity()
                    l.addFoundTrespasser(self.curP, self.curT, founded_tres)
                    self.scene.removeItem(founded_tres)
                    self.number_t_detected = self.number_t_detected + 1
                    item = QTableWidgetItem()
                    item.setData(Qt.DisplayRole, self.number_t_detected)
                    self.result1Tbl.setItem(self.curP - 1, 3, item)
                    # l.isFoundTrespasser = True
                else:
                    self.trespasser_found = False
                    founded_entity = l.getInvestigatedEntity()
                    self.scene.removeItem(founded_entity)
                # reset investigated entity to none
                l.setInvestigatedEntity(None)
                # determine patrol plan after exiting an investigation
                # if self.patrol_move_model == 1 or self.patrol_move_model == 2:
                #     self.barrierPath(l, self.curT)
                # elif self.patrol_move_model == 3 or self.patrol_move_model == 4:
                #     self.heuristicPath(l, self.curT)

        else:
            l_point = l.pos()
            s_cur = l.getCurLoc()
            if s_cur.getTd() >= 1.0:
                print("invalid move")
            # if self.patrol_move_model != 0:
            s = l.getSegmentFromPlan(self.curT)
            l.setPos(l_point.x() + (s.getCol() - s_cur.getCol()) * self.grid_width,
                     l_point.y() + (s.getRow() - s_cur.getRow()) * self.grid_width)
            l.setCurLoc(s)
            l.setPrevLoc(s_cur)
            s.setPFp(0)
            s.setLastPatrolledBy(l)
            s.setLastPatrolledAt(self.curT)
            ss = l.getFPSensor()
            if ss:
                ss.setPos(l_point.x() + (s.getCol() - s_cur.getCol()) * self.grid_width,
                          l_point.y() + (s.getRow() - s_cur.getRow()) * self.grid_width)
                ss.setLoc(s)
            self.detectionProcess(l)
            # else:
            #     surroundings = self.findSurrounding(s_cur.getRow(), s_cur.getCol())
            #     d_random = np.random.choice(surroundings, 1)
            #     s_random = d_random[0]["obj"]
            #     l.setPos(l_point.x() + (s_random.getCol() - s_cur.getCol()) * self.grid_width,
            #              l_point.y() + (s_random.getRow() - s_cur.getRow()) * self.grid_width)
            #     l.setCurLoc(s_random)
            #     s_random.setPFp(0)
            #     s_random.setLastPatrolledBy(l)
            #     s_random.setLastPatrolledAt(self.curT)

    def detectionProcess(self, l):
        p_loc = l.getCurLoc()
        p_prev = l.getPrevLoc()
        for k in self.trespassers:
            k_loc = k.getCurLoc()
            k_prev = k.getPrevLoc()
            if (p_loc == k_loc or (p_prev == k_loc and p_loc == k_prev)) and k.getStatus() == 1 and l.getStatus() == 1:
                detection_result = np.random.choice([0, 1],
                                                    p=[1 - self.detection_coef * (1 - p_loc.getOb()),
                                                       self.detection_coef * (1 - p_loc.getOb())])
                if detection_result == 1:
                    k.setStatus(2)
                    l.setStatus(2)
                    l.setInvestigatedEntity(k)
                    # remove footprint generated by k
                    for d in self.segments:
                        if d["obj"].getLastTrespassedBy() == k:
                            d["obj"].setLastTrespassedBy(None)
                            d["obj"].setTFp(np.inf)
                    # delay plan for t_I stages
                    for t in range(self.investigation_time):
                        l.delayPlan(p_loc)
                        l.setReplanStage(l.getReplanStage() + 1)

        for n in self.noises:
            n_loc = n.getCurLoc()
            n_prev = n.getPrevLoc()
            if (p_loc == n_loc or (p_prev == n_loc and p_loc == n_prev)) and n.getStatus() == 1 and l.getStatus() == 1:
                detection_result = np.random.choice([0, 1],
                                                    p=[1 - self.detection_coef * (1 - p_loc.getOb()),
                                                       self.detection_coef * (1 - p_loc.getOb())])
                if detection_result == 1:
                    n.setStatus(2)
                    l.setStatus(2)
                    l.setInvestigatedEntity(n)
                    # delay plan for t_I stages
                    for t in range(self.investigation_time):
                        l.delayPlan(p_loc)
                        l.setReplanStage(l.getReplanStage() + 1)

    def rePlanningProcess(self, l):
        if l.getReplanStage() == self.curT and l.getStatus() == 1:
            print("%s replans at stage %i" % (l.getId(), self.curT))
            comm_result = np.random.choice([0, 1], p=[1 - self.comm_success_rate, self.comm_success_rate])
            if comm_result == 1:
                l.copySegmentsInfo(self.segments)
                l.setRecordedStat(self.accu_tres)
            if self.patrol_move_model == 1 or self.patrol_move_model == 2:
                self.barrierPath(l, self.curT)
            elif self.patrol_move_model == 3 or self.patrol_move_model == 4:
                self.heuristicPath(l, self.curT)
            else:
                self.randomPath(l, self.curT)

    def resetFootprintVal(self):
        for d in self.segments:
            d["obj"].setTFp(np.inf)
            d["obj"].setPFp(np.inf)
            d["obj"].setLastPatrolledBy(None)
            d["obj"].setLastTrespassedBy(None)

    def generateTrespassers(self):
        for t in self.trespassers:
            if t.getStatus() == 1:
                self.scene.removeItem(t)
        self.trespassers = []
        # Poisson number of arrivals in a period
        n = np.random.poisson(self.trespasser_arrival_rate)
        entries = [d for d in self.segments if d["col"] == 1 and d["obj"].getTd() < 1]
        exits = [d for d in self.segments if d["col"] == self.number_col and d["obj"].getTd() < 1]
        # if n > 0:
        # with parallel_backend('threading', n_jobs=n):
        #     results = Parallel()(delayed(self.genOneTrespasser)(i, entries, exits) for i in range(n))
        #     self.trespassers = results
        num_m0 = int(np.ceil(self.trespasser_move_model[0] * n))
        num_m1 = int(np.ceil(self.trespasser_move_model[1] * n))
        num_m2 = int(np.ceil(self.trespasser_move_model[2] * n))
        for i in range(num_m0):
            self.trespassers.append(self.genOneTrespasser(i, entries, exits, 0))
        for i in range(num_m0, num_m0+num_m1):
            self.trespassers.append(self.genOneTrespasser(i, entries, exits, 1))
        for i in range(num_m0+num_m1, num_m0+num_m1+num_m2):
            self.trespassers.append(self.genOneTrespasser(i, entries, exits, 2))

    def genOneTrespasser(self, i, entries, exits, mm):
        # trespasser's poisson arrival time
        arr_time = np.floor(np.random.uniform(1, self.period_len))
        # random select entry segment
        entry_s = np.random.choice(entries)
        exit_s = np.random.choice(exits)
        s_en = entry_s["obj"]
        s_ex = exit_s["obj"]
        # add new trespasser
        trespasser = TrespasserAgent('tres_' + str(i + 1), s_en, s_ex, arr_time,
                                     self.pos_x + (int(s_en.getCol() - 1) * self.grid_width),
                                     self.pos_y + (int(s_en.getRow()) - 1) * self.grid_width,
                                     self.grid_width, self.grid_width)
        # mm = np.random.choice([0, 1, 2], p=self.trespasser_move_model)
        trespasser.setMoveModel(mm)
        if mm != 0:
            self.findTrespasserPath(trespasser, s_en, s_ex)
        # else:
        #     self.findRandomTrespassingPaths(trespasser, s_en, s_ex)

        return trespasser

    def generateNoise(self):
        for n in self.noises:
            if n.getStatus() == 1:
                self.scene.removeItem(n)
        self.noises = []
        # Poisson number of arrivals in a period
        n = np.random.poisson(self.trespasser_arrival_rate * self.noise_rate / 100)
        entries = [d for d in self.segments if d["obj"].getTd() < 1]
        # exits = [d for d in self.segments if d["col"] == self.number_col and d["obj"].getTd() < 1]
        # if n > 0:
        for i in range(n):
            self.noises.append(self.genOneNoise(i, entries))
            # with parallel_backend('threading', n_jobs=n):
            #     results = Parallel()(delayed(self.genOneNoise)(i, entries) for i in range(n))
            #     self.noises = results

    def genOneNoise(self, i, entries):
        # trespasser's poisson arrival time
        arr_time = np.floor(np.random.uniform(1, self.period_len))
        # random select entry segment
        entry_s = np.random.choice(entries)
        s_en = entry_s["obj"]
        # add new trespasser
        noise = Noise('noise_' + str(i + 1), s_en, arr_time,
                      self.pos_x + (int(s_en.getCol() - 1) * self.grid_width),
                      self.pos_y + (int(s_en.getRow()) - 1) * self.grid_width,
                      self.grid_width, self.grid_width)
        return noise

    def generatePatrolPlan(self):
        if self.num_patrol:
            for p in self.patrols:
                self.genOnePatrolInitPlan(p)
            # with parallel_backend('threading', n_jobs=self.num_patrol):
            #     Parallel()(delayed(self.genOnePatrolInitPlan)(p) for p in self.patrols)

    def genOnePatrolInitPlan(self, p):
        p.copySegmentsInfo(self.segments)
        p.setRecordedStat(self.accu_tres)
        if self.patrol_move_model == 1 or self.patrol_move_model == 2:
            self.barrierPath(p, 0)
        elif self.patrol_move_model == 3 or self.patrol_move_model == 4:
            self.heuristicPath(p, 0)
        else:
            self.randomPath(p, 0)

    def findRandomTrespassingPaths(self, t, en, ex):
        # incompleted_paths = []
        # completed_paths = []
        #
        # path = []
        # path.append(en)
        # incompleted_paths.append(path)
        #
        # while len(incompleted_paths) > 0:
        #
        #     path = incompleted_paths[-1]
        #     endpoint = path[-1]
        #     if endpoint.getCol() == self.number_col and endpoint.getTd() < 1:
        #         incompleted_paths.remove(path)
        #         completed_paths.append(path)
        #
        #     else:
        #
        #         dd = self.findSurrounding(endpoint.getRow(), endpoint.getCol())
        #         path_found = 0
        #         for d in dd:
        #             if not [s for s in path if s == d["obj"]]:
        #                 path_found = path_found + 1
        #                 if path_found == 1:
        #                     path.append(d["obj"])
        #                 else:
        #                     new_path = path[:-1]
        #                     new_path.append(d["obj"])
        #                     incompleted_paths.append(new_path)
        #
        #         if path_found == 0:
        #             incompleted_paths.remove(path)
        #

        # construct graph
        g = Graph()
        for x in range(1, self.number_row + 1):
            for y in range(1, self.number_col + 1):
                d = self.findSegment(x, y)
                if d["obj"].getTd() < 1.0:
                    g.add_vertex(str(x) + ',' + str(y), x, y)

        vertice_keys = g.get_vertices()
        visited = {}
        for key in vertice_keys:
            visited[key] = False
            vertex = g.get_vertex(key)
            # print(vertex)
            v_i = vertex.get_i()
            v_j = vertex.get_j()
            # v_1 = self.findSegment(v_i - 1, v_j - 1)
            v_2 = self.findSegment(v_i - 1, v_j)
            v_3 = self.findSegment(v_i - 1, v_j + 1)
            v_4 = self.findSegment(v_i, v_j + 1)
            v_5 = self.findSegment(v_i + 1, v_j + 1)
            v_6 = self.findSegment(v_i + 1, v_j)
            # v_7 = self.findSegment(v_i + 1, v_j - 1)
            # v_8 = self.findSegment(v_i, v_j - 1)
            # if (v_i - 1 >= 1 and v_j - 1 >= 1) and v_1["obj"].getTd() < 1:
            #     next_vertex = g.get_vertex(str(v_i - 1) + ',' + str(v_j - 1))
            #     cost = 0
            #     g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i - 1 >= 1) and v_2["obj"].getTd() < 1:
                next_vertex = g.get_vertex(str(v_i - 1) + ',' + str(v_j))
                cost = 0
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i - 1 >= 1 and v_j + 1 <= self.number_col) and v_3["obj"].getTd() < 1:
                next_vertex = g.get_vertex(str(v_i - 1) + ',' + str(v_j + 1))
                cost = 0
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_j + 1 <= self.number_col) and v_4["obj"].getTd() < 1:
                next_vertex = g.get_vertex(str(v_i) + ',' + str(v_j + 1))
                cost = 0
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i + 1 <= self.number_row and v_j + 1 <= self.number_col) and v_5["obj"].getTd() < 1:
                next_vertex = g.get_vertex(str(v_i + 1) + ',' + str(v_j + 1))
                cost = 0
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i + 1 <= self.number_row) and v_6["obj"].getTd() < 1:
                next_vertex = g.get_vertex(str(v_i + 1) + ',' + str(v_j))
                cost = 0
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            # if (v_i + 1 <= self.number_row and v_j - 1 >= 1) and v_7["obj"].getTd() < 1:
            #     next_vertex = g.get_vertex(str(v_i + 1) + ',' + str(v_j - 1))
            #     cost = 0
            #     g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            # if (v_j - 1 >= 1) and v_8["obj"].getTd() < 1:
            #     next_vertex = g.get_vertex(str(v_i) + ',' + str(v_j - 1))
            #     cost = 0
            #     g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)

        path = []
        path_list = []
        self.findPathUtil(g, en, ex, visited, path, path_list)

        # sel_path = path_list[0]
        sel_path = np.random.choice(path_list)
        print("select trespasser path for %s" % t.getId())
        print(sel_path)
        stage = t.getArrTime()
        for s in sel_path:
            t.addToPlan(stage, s)
            stage = stage + 1

    def findPathUtil(self, g, u, d, visited, path, path_list):

        if len(path_list) >= 3:
            return

        u_key = str(u.getRow()) + ',' + str(u.getCol())
        u_vertex = g.get_vertex(u_key)
        visited[u_key] = True
        path.append(u)

        if u == d or u.getCol() == self.number_col:
            path_c = []
            for e in path:
                path_c.append(e)
            path_list.append(path_c)
        else:
            adj = []
            for v in u_vertex.adjacent:
                adj.append(v)
            adj_ = sample(adj, len(adj))
            for v in adj_:
                if visited[v.get_id()] == False and v.get_j() >= u_vertex.get_j():
                    [i, j] = v.get_id().split(",")
                    s = self.findSegment(int(i), int(j))
                    self.findPathUtil(g, s["obj"], d, visited, path, path_list)

        path.pop()
        visited[u_key] = False

    def findTrespasserPath(self, t, en, ex):
        # construct graph
        g = Graph()
        for x in range(1, self.number_row + 1):
            for y in range(1, self.number_col + 1):
                d = self.findSegment(x, y)
                if d["obj"].getTd() < 1.0:
                    g.add_vertex('a_(' + str(x) + ',' + str(y) + ')', x, y)

        vertice_keys = g.get_vertices()
        for key in vertice_keys:
            vertex = g.get_vertex(key)
            # print(vertex)
            v_i = vertex.get_i()
            v_j = vertex.get_j()
            v_1 = self.findSegment(v_i - 1, v_j - 1)
            v_2 = self.findSegment(v_i - 1, v_j)
            v_3 = self.findSegment(v_i - 1, v_j + 1)
            v_4 = self.findSegment(v_i, v_j + 1)
            v_5 = self.findSegment(v_i + 1, v_j + 1)
            v_6 = self.findSegment(v_i + 1, v_j)
            v_7 = self.findSegment(v_i + 1, v_j - 1)
            v_8 = self.findSegment(v_i, v_j - 1)
            if (v_i - 1 >= 1 and v_j - 1 >= 1) and v_1["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i - 1) + ',' + str(v_j - 1) + ')')
                cost = t.getWTd() * v_1["obj"].getTd() + t.getWOb() * (1 - v_1["obj"].getOb()) + \
                       t.getWSt() * (1 - v_1["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i - 1 >= 1) and v_2["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i - 1) + ',' + str(v_j) + ')')
                cost = t.getWTd() * v_2["obj"].getTd() + t.getWOb() * (1 - v_2["obj"].getOb()) + \
                       t.getWSt() * (1 - v_2["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i - 1 >= 1 and v_j + 1 <= self.number_col) and v_3["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i - 1) + ',' + str(v_j + 1) + ')')
                cost = t.getWTd() * v_3["obj"].getTd() + t.getWOb() * (1 - v_3["obj"].getOb()) + \
                       t.getWSt() * (1 - v_3["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_j + 1 <= self.number_col) and v_4["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i) + ',' + str(v_j + 1) + ')')
                cost = t.getWTd() * v_4["obj"].getTd() + t.getWOb() * (1 - v_4["obj"].getOb()) + \
                       t.getWSt() * (1 - v_4["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i + 1 <= self.number_row and v_j + 1 <= self.number_col) and v_5["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i + 1) + ',' + str(v_j + 1) + ')')
                cost = t.getWTd() * v_5["obj"].getTd() + t.getWOb() * (1 - v_5["obj"].getOb()) + \
                       t.getWSt() * (1 - v_5["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i + 1 <= self.number_row) and v_6["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i + 1) + ',' + str(v_j) + ')')
                cost = t.getWTd() * v_6["obj"].getTd() + t.getWOb() * (1 - v_6["obj"].getOb()) + \
                       t.getWSt() * (1 - v_6["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i + 1 <= self.number_row and v_j - 1 >= 1) and v_7["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i + 1) + ',' + str(v_j - 1) + ')')
                cost = t.getWTd() * v_7["obj"].getTd() + t.getWOb() * (1 - v_7["obj"].getOb()) + \
                       t.getWSt() * (1 - v_7["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_j - 1 >= 1) and v_8["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i) + ',' + str(v_j - 1) + ')')
                cost = t.getWTd() * v_8["obj"].getTd() + t.getWOb() * (1 - v_8["obj"].getOb()) + \
                       t.getWSt() * (1 - v_8["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)

        dijk = Dijkstra(g)
        entry_vertex = 'a_(' + str(en.getRow()) + ',1)'
        exit_vertex = 'a_(' + str(ex.getRow()) + ',' + str(self.number_col) + ')'
        traversed_g = dijk.traversing(entry_vertex, exit_vertex)
        end_vertex = traversed_g.get_vertex(exit_vertex)
        path = [end_vertex]
        dijk.shortest(end_vertex, path)
        stage = t.getArrTime()
        for s in path[::-1]:
            d = self.findSegment(s.get_i(), s.get_j())
            t.addToPlan(stage, d["obj"])
            stage = stage + 1

    def findTrespasserPathWithFP(self, t, en, ex):
        # construct graph
        g = Graph()
        for x in range(1, self.number_row + 1):
            for y in range(1, self.number_col + 1):
                d = self.findSegment(x, y)
                if d["obj"].getTd() < 1.0:
                    g.add_vertex('a_(' + str(x) + ',' + str(y) + ')', x, y)

        vertice_keys = g.get_vertices()
        sum_belief = sum([b.getL() for b in t.getBelief()])
        for key in vertice_keys:
            vertex = g.get_vertex(key)
            # print(vertex)
            v_i = vertex.get_i()
            v_j = vertex.get_j()
            v_1 = self.findSegment(v_i - 1, v_j - 1)
            v_2 = self.findSegment(v_i - 1, v_j)
            v_3 = self.findSegment(v_i - 1, v_j + 1)
            v_4 = self.findSegment(v_i, v_j + 1)
            v_5 = self.findSegment(v_i + 1, v_j + 1)
            v_6 = self.findSegment(v_i + 1, v_j)
            v_7 = self.findSegment(v_i + 1, v_j - 1)
            v_8 = self.findSegment(v_i, v_j - 1)
            if (v_i - 1 >= 1 and v_j - 1 >= 1) and v_1["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i - 1) + ',' + str(v_j - 1) + ')')
                if v_1["obj"] in t.getBelief():
                    cost = t.getWTd() * v_1["obj"].getTd() + t.getWOb() * (1 - v_1["obj"].getOb()) + \
                           t.getWSt() * (1 - v_1["obj"].getSt() / self.accu_tres) + v_1["obj"].getL() / sum_belief
                else:
                    cost = t.getWTd() * v_1["obj"].getTd() + t.getWOb() * (1 - v_1["obj"].getOb()) + \
                           t.getWSt() * (1 - v_1["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i - 1 >= 1) and v_2["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i - 1) + ',' + str(v_j) + ')')
                if v_2["obj"] in t.getBelief():
                    cost = t.getWTd() * v_2["obj"].getTd() + t.getWOb() * (1 - v_2["obj"].getOb()) + \
                           t.getWSt() * (1 - v_2["obj"].getSt() / self.accu_tres) + v_2["obj"].getL() / sum_belief
                else:
                    cost = t.getWTd() * v_2["obj"].getTd() + t.getWOb() * (1 - v_2["obj"].getOb()) + \
                           t.getWSt() * (1 - v_2["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i - 1 >= 1 and v_j + 1 <= self.number_col) and v_3["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i - 1) + ',' + str(v_j + 1) + ')')
                if v_3["obj"] in t.getBelief():
                    cost = t.getWTd() * v_3["obj"].getTd() + t.getWOb() * (1 - v_3["obj"].getOb()) + \
                           t.getWSt() * (1 - v_3["obj"].getSt() / self.accu_tres) + v_3["obj"].getL() / sum_belief
                else:
                    cost = t.getWTd() * v_3["obj"].getTd() + t.getWOb() * (1 - v_3["obj"].getOb()) + \
                           t.getWSt() * (1 - v_3["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_j + 1 <= self.number_col) and v_4["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i) + ',' + str(v_j + 1) + ')')
                if v_4["obj"] in t.getBelief():
                    cost = t.getWTd() * v_4["obj"].getTd() + t.getWOb() * (1 - v_4["obj"].getOb()) + \
                           t.getWSt() * (1 - v_4["obj"].getSt() / self.accu_tres) + v_4["obj"].getL() / sum_belief
                else:
                    cost = t.getWTd() * v_4["obj"].getTd() + t.getWOb() * (1 - v_4["obj"].getOb()) + \
                           t.getWSt() * (1 - v_4["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i + 1 <= self.number_row and v_j + 1 <= self.number_col) and v_5["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i + 1) + ',' + str(v_j + 1) + ')')
                if v_5["obj"] in t.getBelief():
                    cost = t.getWTd() * v_5["obj"].getTd() + t.getWOb() * (1 - v_5["obj"].getOb()) + \
                           t.getWSt() * (1 - v_5["obj"].getSt() / self.accu_tres) + v_5["obj"].getL() / sum_belief
                else:
                    cost = t.getWTd() * v_5["obj"].getTd() + t.getWOb() * (1 - v_5["obj"].getOb()) + \
                           t.getWSt() * (1 - v_5["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i + 1 <= self.number_row) and v_6["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i + 1) + ',' + str(v_j) + ')')
                if v_6["obj"] in t.getBelief():
                    cost = t.getWTd() * v_6["obj"].getTd() + t.getWOb() * (1 - v_6["obj"].getOb()) + \
                           t.getWSt() * (1 - v_6["obj"].getSt() / self.accu_tres) + v_6["obj"].getL() / sum_belief
                else:
                    cost = t.getWTd() * v_6["obj"].getTd() + t.getWOb() * (1 - v_6["obj"].getOb()) + \
                           t.getWSt() * (1 - v_6["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_i + 1 <= self.number_row and v_j - 1 >= 1) and v_7["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i + 1) + ',' + str(v_j - 1) + ')')
                if v_7["obj"] in t.getBelief():
                    cost = t.getWTd() * v_7["obj"].getTd() + t.getWOb() * (1 - v_7["obj"].getOb()) + \
                           t.getWSt() * (1 - v_7["obj"].getSt() / self.accu_tres) + v_7["obj"].getL() / sum_belief
                else:
                    cost = t.getWTd() * v_7["obj"].getTd() + t.getWOb() * (1 - v_7["obj"].getOb()) + \
                           t.getWSt() * (1 - v_7["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
            if (v_j - 1 >= 1) and v_8["obj"].getTd() < 1:
                next_vertex = g.get_vertex('a_(' + str(v_i) + ',' + str(v_j - 1) + ')')
                if v_8["obj"] in t.getBelief():
                    cost = t.getWTd() * v_8["obj"].getTd() + t.getWOb() * (1 - v_8["obj"].getOb()) + \
                           t.getWSt() * (1 - v_8["obj"].getSt() / self.accu_tres) + v_8["obj"].getL() / sum_belief
                else:
                    cost = t.getWTd() * v_8["obj"].getTd() + t.getWOb() * (1 - v_8["obj"].getOb()) + \
                           t.getWSt() * (1 - v_8["obj"].getSt() / self.accu_tres)
                g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)

        dijk = Dijkstra(g)
        entry_vertex = 'a_(' + str(en.getRow()) + ',1)'
        exit_vertex = 'a_(' + str(ex.getRow()) + ',' + str(self.number_col) + ')'
        traversed_g = dijk.traversing(entry_vertex, exit_vertex)
        end_vertex = traversed_g.get_vertex(exit_vertex)
        path = [end_vertex]
        dijk.shortest(end_vertex, path)
        stage = t.getArrTime()
        for s in path[::-1]:
            d = self.findSegment(s.get_i(), s.get_j())
            t.addToPlan(stage, d["obj"])
            stage = stage + 1

    def randomPath(self, p, t):
        s_c = p.getCurLoc()
        p.resetPlan()
        # p.addToPlan(t, s_c)
        for tt in range(t + 1, t + self.planning_stages + 1):
            if self.zoning:
                d_k = self.findSurroundingInZone(p, s_c.getRow(), s_c.getCol())
            else:
                d_k = self.findSurrounding(s_c.getRow(), s_c.getCol())

            d_c = np.random.choice(d_k)
            s_c = d_c["obj"]
            p.addToPlan(tt, s_c)
        p.setReplanStage(t + self.planning_stages)

    def barrierPath(self, p, t):
        s_c = p.getCurLoc()
        p.resetPlan()
        # p.addToPlan(t, s_c)
        direction = np.random.choice([-1, 1])
        for tt in range(t + 1, t + self.planning_stages + 1):
            if direction > 0:
                d_a = self.findUpSegment(s_c.getRow(), s_c.getCol())
                if d_a:
                    s_c = d_a[0]["obj"]
                else:
                    direction = direction * -1
            else:
                d_a = self.findDownSegment(s_c.getRow(), s_c.getCol())
                if d_a:
                    s_c = d_a[0]["obj"]
                else:
                    direction = direction * -1

            p.addToPlan(tt, s_c)
        p.setReplanStage(t + self.planning_stages)

    def heuristicPath(self, p, t):
        s_c = p.getCurLoc()
        s_cc = p.findRecordedSegment(s_c.getRow(), s_c.getCol())
        m_c = p.getWTd() * (1 - s_cc.getTd()) + p.getWOb() * s_cc.getOb() + \
              p.getWSt() * s_cc.getSt() / p.getRecordedStat()
        pa = PatrolPath()
        pa.addPatrolCell(s_c, m_c)
        p.setPl([])
        p.addPath(pa)
        # p.addToPlan(1, s_c)
        for k in range(t + 1, t + self.planning_stages + 1):
            pl = p.getPl()
            pll = []
            for pa_ in pl:
                s_end = pa_.getEndPoint()
                if self.zoning:
                    d_k = self.findSurroundingInZone(p, s_end.getRow(), s_end.getCol())
                else:
                    d_k = self.findSurrounding(s_end.getRow(), s_end.getCol())

                for dd_k in d_k:
                    paa = PatrolPath()
                    for cell in pa_.getCells():
                        paa.addPatrolCell(cell, 0)
                    paa.setAggM(pa_.getAggM())
                    paa.setLength(pa_.getLength())
                    guards = paa.getRepeatGuardSegments(self.repeat_guard)

                    if (dd_k["obj"] in guards) or (dd_k["obj"].getLastPatrolledBy() and
                                                   dd_k["obj"].getLastPatrolledAt() + self.repeat_guard > self.curT):
                        m_k = 0
                    else:
                        s_kk = p.findRecordedSegment(dd_k["obj"].getRow(), dd_k["obj"].getCol())
                        m_k = p.getWTd() * (1 - s_kk.getTd()) + p.getWOb() * s_kk.getOb() + \
                              p.getWSt() * s_kk.getSt() / p.getRecordedStat()
                    paa.addPatrolCell(dd_k["obj"], m_k)
                    pll.append(paa)

            p.setPl(pll)

        max_pa = max(p.getPl(), key=lambda pa: pa.getAggM())
        # sel_pa = max_pa[0]
        tt = t
        p.resetPlan()
        for cell in max_pa.getCells():
            p.addToPlan(tt, cell)
            tt = tt + 1
        p.setReplanStage(t + self.planning_stages)

    def POMDPPlanning(self, p):
        p.resetPlan()
        b0 = p.getBelief()
        sum_b0 = sum([p.getWTd() * (1 - g.getTd()) + p.getWOb() * g.getOb() + p.getWSt() * g.getSt() / self.accu_tres
                      for g in b0])
        p_b0 = [
            (p.getWTd() * (1 - g.getTd()) + p.getWOb() * g.getOb() + p.getWSt() * g.getSt() / self.accu_tres) / sum_b0
            for g in b0]
        # prune tree
        p.T = {}
        # explored belief
        p.explored_b = []
        # initialize tree
        p.explored_b.append(b0)
        p.T[(b0, 0)] = {"N": 0, "V": 0, "parent": None}

        # simulate for many rounds
        for i in range(self.mcts_simulations):
            s0_i = np.random.choice(b0, p=p_b0)
            self.MCTSSimulate(p, s0_i, b0, 0)
        # randomly select one location from belief

    def MCTSSimulate(self, p, s_i, b_i, d):
        gamma = 10 ** -1
        epsilon = 10 ** -12
        if gamma ** d < epsilon:
            return 0
        # if not [b for b in p.explored_b]:
        # for


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(15, 15, 15))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(222, 44, 124))
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)

    palette.setColor(QPalette.Highlight, QColor(222, 44, 124).lighter())
    palette.setColor(QPalette.HighlightedText, QColor(53, 53, 53))
    app.setPalette(palette)

    window = BorderSim()
    sys.exit(app.exec_())
