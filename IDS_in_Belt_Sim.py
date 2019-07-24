import sys
import numpy as np
import scipy.special as sp
import operator
import csv
import sip
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from functools import partial
sip.setapi('QString',2)
sip.setapi('QVariant',2)

class IDSSim(QWidget):
    def __init__(self):
        super().__init__()

        self.sensors = {"sensors":[]}
        self.truetargets = {"trespassers":[]}
        self.falsetargets = {"trespassers":[]}
        self.segments = {"segments":[]}
        self.entry_segments = []
        self.entry_prob = []
        self.totalStat = 0
        self.targetlifetime = 0.5 #target is active after time period

        self.number_ientry = 0    #number of intruder entering the area during the period
        self.number_tentry = 0    #number of regular trespasser entering the area during the period
        self.number_iexit_a = 0   #number of intruder exiting the area through the exit line
        self.number_texit_a = 0
        self.number_iexit_b = 0   #number of intruder exiting the area through the sides
        self.number_idetected = 0 #number of intruder detected by a sensors (true detection)
        self.number_tdetected = 0 #number of intruder detected by a sensors (false detection)

        layout = QHBoxLayout()      
        self.setBeltRegion()
        self.createTabView()
        layout.addWidget(self.view)
        layout.addWidget(self.tabView)
        self.timer = QTimer()
        self.curT = 0
        #connect(self.timer, SIGNAL(timeout()), this, SLOT(doSimulation()))
        self.timer.timeout.connect(self.doSimulation) 
        self.setLayout(layout)
        self.setFixedSize(1400,800)
        self.show()

    def setBeltRegion(self):
        self.pos_x = 10
        self.pos_y = 10
        self.grid_width = 10
        self.number_w = 0
        self.number_h = 0
        self.sensorSchema = "random"
        self.movementSchema = "stationary"
        
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QColor(0,0,0,255))
       
        self.view = QGraphicsView(self)
        self.view.setFixedSize(500,800)
        self.view.setSceneRect(0,0,500,800)
        
        self.view.fitInView(0,0,500,800,Qt.KeepAspectRatio)
        
        self.view.setScene(self.scene)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    def drawGrid(self):
        self.number_w = self.dimensionW.value()
        self.number_h = self.dimensionH.value()
        
        for s in self.segments["segments"]:
            self.scene.removeItem(s["obj"].getGrid())
            
        self.segments = {"segments":[]}
        for j in range(0,self.number_h):
            self.entry_segments.append(j+1)
            for i in range(0,self.number_w):
                #rect = segmentObj(self.pos_x+i*self.grid_width,self.pos_y+j*self.grid_width,self.grid_width,self.grid_width,i+1,j+1)
                rect = self.scene.addRect(self.pos_x+i*self.grid_width,self.pos_y+j*self.grid_width,self.grid_width,self.grid_width,QColor(Qt.white),QBrush(Qt.NoBrush))
                #rect.clicked.connect(lambda:self.openSegmentDialog(i,j))
                rect.setPen(QColor(Qt.white))
                rect.setBrush(QBrush(Qt.NoBrush))
                
                #self.scene.addItem(rect)
                #segment = {}
                #segment["id"]="A"+"_"+str(j)+"_"+str(i)
                #segment["c"]=0
                #segment["o"]=0
                #segment["s"]=0
                #segment["segmentObj"]=rect
                #h = self.likelihood(1,(i+1)*self.grid_width)
                
                #h = (1/(0.5*self.number_w))*np.exp(-(self.number_w-i+1)/(0.5*self.number_w))
                h = np.exp(-1*(self.number_w-i+1))
                #h = 0

                rect.setToolTip("b: %f o: %f s: %i h: %f" % (0.5,0,0,h))
                segment = segmentObj(i+1,j+1,0.5,0,0,h,rect)
                self.segments["segments"].append({"key":segment.getId(),"obj":segment})

        
        self.view.setScene(self.scene)

    def likelihood(self,type,distance):
        #type of trespasser
        #distance from exit line in number of segments unit
        #if type==1:
            #mu = 1*self.grid_width*self.number_w
            #var = 0.7*self.grid_width*self.number_w
            #pdf = (1/np.sqrt(2*np.power(var,2)*np.pi))*np.exp(-1*np.power(distance-mu,2)/(2*np.power(var,2)))
            #cdf_a = 0.5*(1+sp.erf((0-mu)/(np.sqrt(2)*var)))
            #cdf_b = 0.5*(1+sp.erf((self.grid_width*self.number_w-mu)/(np.sqrt(2)*var)))
            #return pdf/(cdf_b-cdf_a)
        return (distance+1)/self.number_w
                #else:
            #mu = 0.3*self.grid_width*self.number_w
            #var = 0.1*self.grid_width*self.number_w
            #pdf = (1/np.sqrt(2*np.power(var,2)*np.pi))*np.exp(-1*np.power(distance-mu,2)/(2*np.power(var,2)))
            #cdf_a = 0.5*(1+sp.erf((0-mu)/(np.sqrt(2)*var)))
            #cdf_b = 0.5*(1+sp.erf((self.grid_width*self.number_w-mu)/(np.sqrt(2)*var)))
            #return pdf/(cdf_b-cdf_a)
                                                           
    def openSegmentDialog(self,w,h):
        d = QDialog()
        layout = QFormLayout()
        b1 = QPushButton("Add a sensor to this segment A_%i_%i" % (w,h))
        layout.addRow(b1)
        d.setLayout(layout)
        
        
    def placeSensors(self):
        for s in self.sensors["sensors"]:
            self.scene.removeItem(s.getNode())
            for i in range(1,len(s._paths["paths"])+1):
                g_path = s.getGPath(i)
                self.scene.removeItem(g_path)
            

            
        self.sensors = {"sensors":[]}
        
        self.number_s = self.numberSensorsInput.value()
        try:
            if (self.number_w==0 | self.number_h==0):
                raise ValueError
            print("sensor: %s" % self.sensorSchema)
            print("movement: %s" % self.movementSchema)
            if (self.sensorSchema == "random"):
                if self.movementSchema == "single":
                    print("Place sensors randomly on a barrier line")
                    for i in range(0,self.number_s):
                        init_pos_x = np.floor(self.number_w/2)
                        init_pos_y = np.around(np.random.uniform(1,self.number_h))
                        sensor = self.placeSensor(i+1,int(init_pos_x),int(init_pos_y))
                        sensor.setDirX(0)
                        sensor.setDirY(np.random.choice([-1,1],1))
                        print("Place %i,%i" % (init_pos_x,init_pos_y))
                elif self.movementSchema == "double":
                    print("Place sensors randomly on two barrier line")
                    for i in range(0,self.number_s):
                        init_pos_x = np.around(np.random.choice([np.floor(self.number_w/4),np.floor(self.number_w*3/4)],1))
                        init_pos_y = np.around(np.random.uniform(1,self.number_h))
                        sensor = self.placeSensor(i+1,int(init_pos_x),int(init_pos_y))
                        sensor.setDirX(0)
                        sensor.setDirY(np.random.choice([-1,1],1))
                        print("Place %i,%i" % (init_pos_x,init_pos_y))
                else:
                    print("Place sensors randomly")
                    for i in range(0,self.number_s):
                        init_pos_x = np.around(np.random.uniform(1,self.number_w))
                        init_pos_y = np.around(np.random.uniform(1,self.number_h))
                        sensor = self.placeSensor(i+1,int(init_pos_x),int(init_pos_y))
                        print("Place %i,%i" % (init_pos_x,init_pos_y))
                        #node = self.scene.addEllipse(self.pos_x+init_pos_x*self.grid_width-self.grid_width,self.pos_y+init_pos_y*self.grid_width-self.grid_width,self.grid_width*0.8,self.grid_width*0.8,QColor(0,153,255,255),QColor(0,153,255,255))
                        
                        #node = QGraphicsItemGroup()
                        #coverage = self.scene.addEllipse(self.pos_x+(int(init_pos_x)-1-self.coverageRadius.value())*self.grid_width,self.pos_y+(int(init_pos_y)-1-self.coverageRadius.value())*self.grid_width,2*(self.coverageRadius.value()+0.5)*self.grid_width,2*(self.coverageRadius.value()+0.5)*self.grid_width,QColor(0,153,255,255),QColor(0,153,255,100))
                        #coverage = QGraphicsEllipseItem(self.pos_x+(int(init_pos_x)-1-self.coverageRadius.value())*self.grid_width,self.pos_y+(int(init_pos_y)-1-self.coverageRadius.value())*self.grid_width,2*(self.coverageRadius.value()+0.5)*self.grid_width,2*(self.coverageRadius.value()+0.5)*self.grid_width)
                        #coverage.setPen(QColor(0,153,255,255))
                        #coverage.setBrush(QColor(0,153,255,100))
                        #point = self.scene.addEllipse(self.pos_x+(int(init_pos_x)-1)*self.grid_width,self.pos_y+(int(init_pos_y)-1)*self.grid_width,self.grid_width,self.grid_width,QColor(0,153,255,255),QColor(0,153,255,255))
                        #point = QGraphicsEllipseItem(self.pos_x+(int(init_pos_x)-1)*self.grid_width,self.pos_y+(int(init_pos_y)-1)*self.grid_width,self.grid_width,self.grid_width)
                        #point.setPen(QColor(0,153,255,255))
                        #point.setBrush(QColor(0,153,255,255))
                        #node.setToolTip("Sensor %i at A_%i_%i" % (i,init_pos_x,init_pos_y))
                        #node.addToGroup(coverage)
                        #node.addToGroup(point)
                        #self.scene.addItem(node)
                        #sensor = {}
                        #sensor["loc"] = "A_"+str(init_pos_y)+"_"+str(init_pos_x)
                        #sensor["node"] = node
                        #loc = "A_"+str(init_pos_y)+"_"+str(init_pos_x)
                        #loc = self.findSegment(int(init_pos_x),int(init_pos_y))
                        #sensor = sensorObj(loc,node)
                        #self.sensors["sensors"].append(sensor)
            else:
                print("Place sensors manually")
                if self.movementSchema == "single":
                    print("Place sensors randomly on a barrier line")
                    for i in range(0,self.number_s):
                        init_pos_x = np.floor(self.number_w/2)
                        init_pos_y = np.around(np.random.uniform(1,self.number_h))
                        sensor = self.placeSensor(i+1,int(init_pos_x),int(init_pos_y))
                        print("Place %i,%i" % (init_pos_x,init_pos_y))
                elif self.movementSchema == "double":
                    print("Place sensors randomly on two barrier line")
                    for i in range(0,self.number_s):
                        init_pos_x = np.around(np.random.choice([np.floor(self.number_w/4),np.floor(self.number_w*3/4)],1))
                        init_pos_y = np.around(np.random.uniform(1,self.number_h))
                        sensor = self.placeSensor(i+1,int(init_pos_x),int(init_pos_y))
                        print("Place %i,%i" % (init_pos_x,init_pos_y))
                else:
                    #open dialog
                    assignDialog = QDialog()
                    assignLayout = QFormLayout(assignDialog)
                    for i in range(0,self.number_s):
                        sensor = self.placeSensor(i+1,1,1)
                        hbox = QHBoxLayout()
                        col = QSpinBox()
                        col.setRange(1,self.number_w)
                        col.setSingleStep(1)
                        col.setValue(1)
                        col.valueChanged.connect(partial(self.moveSensorWithCol,id=i+1))
                        
                        row = QSpinBox()
                        row.setRange(1,self.number_h)
                        row.setSingleStep(1)
                        row.setValue(1)
                        row.valueChanged.connect(partial(self.moveSensorWithRow,id=i+1))
                        
                        hbox.addWidget(col)
                        hbox.addWidget(row)
                        
                        assignLayout.addRow("Sensor "+str(i+1),hbox)
                    
                    
                    assignDialog.setFixedSize(400,300)
                    assignDialog.exec_()
                
                
        except ValueError:
            print("Invalid number of sensors and dimension")

    def moveSensorWithCol(self,value,id=0):
        sensors = [d for d in self.sensors["sensors"] if d.getId()==id]
        s = sensors[0]
        s_node = s.getNode()
        s_point = s_node.pos()
        print("current coordinate ix: %f iy: %f x: %f y:%f" % (s.getX(), s.getY(), s_point.x(),s_point.y()))
        print("next coordinate ix: %f iy: %f x: %f y: %f" % (value,s.getY(),s_point.x()+(value-s.getX())*self.grid_width,s_point.y()))
        
        s_node.setPos(s_point.x()+(value-s.getX())*self.grid_width,s_point.y())
        #s_point = s_node.pos()
        #s.setStartX(s_point.x())
        s.setCurrentLoc(self.findSegment(value,s.getY()))
        s.setX(value)
    
    def moveSensorWithRow(self,value,id=0):
        sensors = [d for d in self.sensors["sensors"] if d.getId()==id]
        s = sensors[0]
        s_node = s.getNode()
        s_point = s_node.pos()
        
        s_node.setPos(s_point.x(),s_point.y()+(value-s.getY())*self.grid_width)
        #s_point = s_node.pos()
        #s.setStartY(s_point.y())
        s.setCurrentLoc(self.findSegment(s.getX(),value))
        s.setY(value)
    
    def placeSensor(self,id,x,y):
        try:
            if x>self.number_w or x<1 or y>self.number_h or y<1:
                raise ValueError
            init_pos_x = x
            init_pos_y = y
            
            node = QGraphicsItemGroup()
            coverage = QGraphicsEllipseItem(self.pos_x+(int(init_pos_x)-1-self.coverageRadius.value())*self.grid_width,self.pos_y+(int(init_pos_y)-1-self.coverageRadius.value())*self.grid_width,2*(self.coverageRadius.value()+0.5)*self.grid_width,2*(self.coverageRadius.value()+0.5)*self.grid_width)
            coverage.setPen(QColor(0,153,255,255))
            coverage.setBrush(QColor(0,153,255,100))
                
            point = QGraphicsEllipseItem(self.pos_x+(int(init_pos_x)-1)*self.grid_width,self.pos_y+(int(init_pos_y)-1)*self.grid_width,self.grid_width,self.grid_width)
            point.setPen(QColor(0,153,255,255))
            point.setBrush(QColor(0,153,255,255))
            node.setToolTip("Sensor %i" % (id))
            node.addToGroup(coverage)
            node.addToGroup(point)
            self.scene.addItem(node)
            startP = node.pos()
            
            loc = self.findSegment(int(init_pos_x),int(init_pos_y))
            sensor = sensorObj(id,startP.x(),startP.y(),int(init_pos_x),int(init_pos_y),loc,node)
            self.sensors["sensors"].append(sensor)
            return sensor
        except ValueError:
            print("Out of Region")
            return None
    def setSensorSchema(self,b):
        if b == 0:
            self.sensorSchema = "random"
        else:
            self.sensorSchema = "manual"

    def setMovementSchema(self,b):
        print("move change to %i" % b)
        if b == 0:
            self.movementSchema = "stationary"
        elif b == 1:
            self.movementSchema = "random"
        elif b == 2:
            self.movementSchema = "single"
        elif b == 3:
            self.movementSchema = "double"
        elif b == 4:
            self.movementSchema = "significant"

    def setSensorModel(self,b):
        if b == 0:
            self.sensorModel = "ideal"
        elif b == 1:
            self.sensorModel = "realistic"


    def createTabView(self):
        self.tabView = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        
        self.tabView.addTab(self.tab1,"Tab 1")
        self.tabView.addTab(self.tab2,"Tab 2")
        self.tab1UI()
        self.tab2UI()

    def genRandomGridVal(self):
        #print(len(self.segments["segments"]))
        for d in self.segments["segments"]:
            segment = d["obj"]
            #print(segment["id"])
            #dif=np.random.uniform(0,1)
            rate = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            dif=np.random.choice(rate, 1, p=[0.15, 0.15, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05])
            det=np.random.uniform(0,1)
            stat=np.random.randint(0,5)
            #stat=np.random.uniform(0,1)
            #self.totalStat=self.totalStat+stat
            segment.setS(stat)
            segment.setO(det)
            segment.setC(dif)
            rect = segment.getGrid()
            rect.setToolTip("b: %f o: %f s: %i h: %f" % (segment.getC(),segment.getO(),segment.getS(),segment.getH()))

    def modCalM(self,sensor):
        return 0
    def calculateMLevel(self):
        w_c = self.weightC.value()      #weight for b
        w_o = self.weightO.value()      #weight for theta
        w_s = self.weightS.value()      #weight for stat
        w_h = self.weightH.value()      #weight for rel pos
        #totalWeightM = 0
        #find max/min stat
        s_max = max(self.segments["segments"], key=lambda x:x["obj"].getS())
        s_min = min(self.segments["segments"], key=lambda x:x["obj"].getS())
        if s_max["obj"].getS()>s_min["obj"].getS():
            m_total = sum([w_c*x["obj"].getC()+w_o*(1-x["obj"].getO())+w_s*(x["obj"].getS()-s_min["obj"].getS())/(s_max["obj"].getS()-s_min["obj"].getS())+w_h*x["obj"].getH() for x in self.segments["segments"]])
        else:
            m_total = sum([w_c*x["obj"].getC()+w_o*(1-x["obj"].getO())+w_h*x["obj"].getH() for x in self.segments["segments"]])
            #for d in self.segments["segments"]:
            #segment = d["obj"]
            #c = segment.getC()
            #o = segment.getO()
            #s = segment.getS()
            #h = segment.getH()
            #m = w_c*c+w_o*o+w_s*(s-s_min)/(s_max-s_min)
            #segment.setM(m)
            #totalWeightM = totalWeightM+m
            #print(m_total)
        for d in self.segments["segments"]:
            segment = d["obj"]
            if s_max["obj"].getS()>s_min["obj"].getS():
                m = w_c*d["obj"].getC()+w_o*(1-d["obj"].getO())+w_s*(d["obj"].getS()-s_min["obj"].getS())/(s_max["obj"].getS()-s_min["obj"].getS())+w_h*d["obj"].getH()
            else:
                m = w_c*d["obj"].getC()+w_o*(1-d["obj"].getO())+w_h*d["obj"].getH()
            
            segment.setM(m)
            
            #print(segment.getM())
            rect = segment.getGrid()
            rect.setToolTip("b: %f o: %f s: %i h: %f m: %f" % (segment.getC(),segment.getO(),segment.getS(),segment.getH(),segment.getM()))

        #calculate prob of entry_segments
        #total_e = 0
        #e_prob = []
        #for i in self.entry_segments:
        #    key = "A_"+str(i)+"_1"
        #    e_list = [d for d in self.segments["segments"] if d["key"]==key]
        #    e_segment = e_list[0]["obj"]
        #    c = e_segment.getC()
        #    o = e_segment.getO()
        #    s = e_segment.getS()
        #    e = w_c*(1-c)+w_o*(1-o)+w_s*s
        #    total_e = total_e+e
        #    e_prob.append(e)

        #self.entry_prob = np.divide(e_prob,total_e)

    def displayShade(self,view):
        if self.segments == {"segments":[]}:
            return
    
        s_max = max(self.segments["segments"], key=lambda x:x["obj"].getS())
        s_min = min(self.segments["segments"], key=lambda x:x["obj"].getS())
        #print(s_max["obj"].getS())
        for d in self.segments["segments"]:
            segment = d["obj"]
            #print(segment["id"])
            dif = 0
            rect = segment.getGrid()
            print("c: %f" % segment.getC())
            #rect.setToolTip("c: %f o: %f s: %i" % (segment.getC(),segment.getO(),segment.getS()))
            red = 0
            green = 0
            blue = 0
            alpha = 255
            if view==1:
                dif=segment.getC()
                if dif>0:
                    red = 255
                    green = np.floor(dif*255) #255-np.floor((1-dif)*255)
                    blue = 0
                else:
                    red = 0
                    green = 0
                    blue = 0
            elif view==2:
                dif=segment.getO()
                red = 255-np.floor(dif*255)
                green = 0
                blue = 255
            elif view==3:
                #dif=segment.getS()/self.totalStat
                print("s max: %i\n" % s_max["obj"].getS())
                print("s min: %i\n" % s_min["obj"].getS())
                print("s: %i\n" % segment.getS())
                if s_max["obj"].getS()>s_min["obj"].getS():
                    dif=(segment.getS()-s_min["obj"].getS())/(s_max["obj"].getS()-s_min["obj"].getS())
                else:
                    dif=0
                if dif>0:
                    #red = 255-np.floor((1-dif)*255)
                    red = 255-np.floor((dif)*255)
                    green = 255
                    blue = 0
                else:
                    red = 0
                    green = 0
                    blue = 0
            else:
                red = 0
                green = 0
                blue = 0
            #elif view==4:
            #    dif=segment.getM()
            #    red = 255-np.floor(dif*1000*255)
            #    green = 255-np.floor(dif*1000*255)
            #    blue = 0
            
              
            rect.setBrush(QColor(red, green, blue, alpha))

    def calculatePath(self):
        periods = self.numberPeriods.value()
        stages = self.numberStages.value()
        #clear path and graphic
        for s in self.sensors["sensors"]:
            for i in range(1,len(s._paths["paths"])+1):
                g_path = s.getGPath(i)
                self.scene.removeItem(g_path)
            s.clearPath()
        
        for p in range(1,periods+1):
            for s in self.sensors["sensors"]:
                curA = s.getCurrentLoc()
                curX = curA.getPosX()
                curY = curA.getPosY()
                paintpath = QPainterPath()
                paintpath.moveTo(self.pos_x+(curX-1)*self.grid_width+0.5*self.grid_width,self.pos_y+(curY-1)*self.grid_width+0.5*self.grid_width)
                g_path = self.scene.addPath(paintpath,QPen(QColor(0,153,255,255),1,Qt.SolidLine),QBrush(Qt.NoBrush))
                s_path = Path(curA,p,stages)
                s_path.addSegment(0,curA)
                s.addPath(p,s_path,g_path)
                
            for t in range(1,stages+1):
                for s in self.sensors["sensors"]:
                    curA = s.getCurrentLoc()
                    curX = curA.getPosX()
                    curY = curA.getPosY()
                    A_nw = None
                    A_nn = None
                    A_ne = None
                    A_ee = None
                    A_se = None
                    A_ss = None
                    A_sw = None
                    A_ww = None
        
                    if curX>1 and curX<self.number_w and curY>1 and curY<self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==1 and curY==1:
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)
                    elif curX>1 and curX<self.number_w and curY==1:
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==self.number_w and curY==1:
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==self.number_w and curY>1 and curY<self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==self.number_w and curY==self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX>1 and curX<self.number_w and curY==self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==1 and curY==self.number_h:
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                    elif curX==1 and curY>1 and curY<self.number_h:
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)

                    next_arr = [1,2,3,4,5,6,7,8]
                    
                    nextA = None
                    next_idx = 0
                    next_m = [0,0,0,0,0,0,0,0]
                    # A_nw,A_nn,A_ne,A_ee,A_se,A_ss,A_sw,A_ww are current surround segments of sensor s
                    if self.movementSchema=="stationary":
                        next_m = self.findStationaryPath([A_nw,A_nn,A_ne,A_ee,A_se,A_ss,A_sw,A_ww])
                    elif self.movementSchema=="random":
                        next_m = self.findRandomPath([A_nw,A_nn,A_ne,A_ee,A_se,A_ss,A_sw,A_ww])
                    elif (self.movementSchema=="single" or self.movementSchema=="double"):
                        next_m = self.findBarrierPath([A_nw,A_nn,A_ne,A_ee,A_se,A_ss,A_sw,A_ww],s)
                    elif self.movementSchema=="significant":
                        next_m = self.findSignificantPath([A_nw,A_nn,A_ne,A_ee,A_se,A_ss,A_sw,A_ww],p,t)
                    weightSum = np.sum(next_m)
                    print(weightSum)
                    if weightSum>0:
                        next_prob = np.divide(next_m,weightSum)
                        #next_prob = [m_nw/weightSum,m_nn/weightSum,m_ne/weightSum,m_ee/weightSum,m_se/weightSum,m_ss/weightSum,m_sw/weightSum,m_ww/weightSum]
                        next_prob = np.reshape(next_prob,len(next_prob))
                        
                        
                        print("***** %f *****\n" % np.sum(next_prob))
                        next_idx = np.random.choice(8,1,p=next_prob)+1
                        
                        if next_idx==1:
                            #nextA = self.findSegment(curX-1,curY-1)
                            nextA = A_nw
                        elif next_idx==2:
                            #nextA = self.findSegment(curX,curY-1)
                            nextA = A_nn
                        elif next_idx==3:
                            #nextA = self.findSegment(curX+1,curY-1)
                            nextA = A_ne
                        elif next_idx==4:
                            #nextA = self.findSegment(curX+1,curY)
                            nextA = A_ee
                        elif next_idx==5:
                            #nextA = self.findSegment(curX+1,curY+1)
                            nextA = A_se
                        elif next_idx==6:
                            #nextA = self.findSegment(curX,curY+1)
                            nextA = A_ss
                        elif next_idx==7:
                            #nextA = self.findSegment(curX-1,curY+1)
                            nextA = A_sw
                        elif next_idx==8:
                            #nextA = self.findSegment(curX-1,curY)
                            nextA = A_ww
                    
                    
                    
                    if nextA is not None:
                        print("next id is %i select next segment as %s\n" % (next_idx,nextA.getId()))
                        nextX = nextA.getPosX()
                        nextY = nextA.getPosY()
                        
                        g_path = s.getGPath(p)
                        paintpath = g_path.path()
                        
                        paintpath.moveTo(self.pos_x+(curX-1)*self.grid_width+0.5*self.grid_width,self.pos_y+(curY-1)*self.grid_width+0.5*self.grid_width)
                        paintpath.lineTo(self.pos_x+(nextX-1)*self.grid_width+0.5*self.grid_width,self.pos_y+(nextY-1)*self.grid_width+0.5*self.grid_width)
                        g_path.setPath(paintpath)
                    
                    
                    else:
                        print("next id is %i no segment is selected\n" % next_idx)
                        nextA = s.getCurrentLoc()
                                

                    s_path = s.getPath(p)
                    s_path.addSegment(t,nextA)
                    s.setCurrentLoc(nextA)
            
    def findStationaryPath(self,A):
        A_nw = A[0]
        A_nn = A[1]
        A_ne = A[2]
        A_ee = A[3]
        A_se = A[4]
        A_ss = A[5]
        A_sw = A[6]
        A_ww = A[7]
        m_nw = 0
        m_nn = 0
        m_ne = 0
        m_ee = 0
        m_se = 0
        m_ss = 0
        m_sw = 0
        m_ww = 0
        return [m_nw,m_nn,m_ne,m_ee,m_se,m_ss,m_sw,m_ww]
    def findRandomPath(self,A):
        A_nw = A[0]
        A_nn = A[1]
        A_ne = A[2]
        A_ee = A[3]
        A_se = A[4]
        A_ss = A[5]
        A_sw = A[6]
        A_ww = A[7]
        m_nw = 0
        m_nn = 0
        m_ne = 0
        m_ee = 0
        m_se = 0
        m_ss = 0
        m_sw = 0
        m_ww = 0
        if (A_nw is not None) and A_nw.getC()>0:
            m_nw = 1
        if A_nn is not None and A_nn.getC()>0:
            m_nn = 1
        if A_ne is not None and A_ne.getC()>0:
            m_ne = 1
        if A_ee is not None and A_ee.getC()>0:
            m_ee = 1
        if A_se is not None and A_se.getC()>0:
            m_se = 1
        if A_ss is not None and A_ss.getC()>0:
            m_ss = 1
        if A_sw is not None and A_sw.getC()>0:
            m_sw = 1
        if A_ww is not None and A_ww.getC()>0:
            m_ww = 1

        print("m_nw: %f,m_nn: %f,m_ne: %f,m_ee: %f,m_se: %f,m_ss: %f,m_sw: %f,,m_ww: %f\n" % (m_nw,m_nn,m_ne,m_ee,m_se,m_ss,m_sw,m_ww))

        return [m_nw,m_nn,m_ne,m_ee,m_se,m_ss,m_sw,m_ww]
            
    def findBarrierPath(self,A,sensor):
        dirX = 0
        dirY = sensor.getDirY()
        A_nw = A[0]
        A_nn = A[1]
        A_ne = A[2]
        A_ee = A[3]
        A_se = A[4]
        A_ss = A[5]
        A_sw = A[6]
        A_ww = A[7]
        m_nw = 0
        m_nn = 0
        m_ne = 0
        m_ee = 0
        m_se = 0
        m_ss = 0
        m_sw = 0
        m_ww = 0
        if dirY==1:
            if A_nn is not None and A_nn.getC()>0:
                m_nn = 1
                sensor.setDirY(1)
            else: 
                m_ss = 1
                sensor.setDirY(-1)
    
        elif dirY==-1:
            
            if A_ss is not None and A_ss.getC()>0:
                m_ss = 1
                sensor.setDirY(-1)
            else: 
                m_nn = 1
                sensor.setDirY(1)
    
        


        return [m_nw,m_nn,m_ne,m_ee,m_se,m_ss,m_sw,m_ww]
            
    def findSignificantPath(self,A,p,t):
        A_nw = A[0]
        A_nn = A[1]
        A_ne = A[2]
        A_ee = A[3]
        A_se = A[4]
        A_ss = A[5]
        A_sw = A[6]
        A_ww = A[7]
        m_nw = 0
        m_nn = 0
        m_ne = 0
        m_ee = 0
        m_se = 0
        m_ss = 0
        m_sw = 0
        m_ww = 0
        if (A_nw is not None) and A_nw.getC()>0 and (self.findNearSegment(A_nw,p,t) is None):
            m_nw = A_nw.getM()
        if A_nn is not None and A_nn.getC()>0 and (self.findNearSegment(A_nn,p,t) is None):
            m_nn = A_nn.getM()
        if A_ne is not None and A_ne.getC()>0 and (self.findNearSegment(A_ne,p,t) is None):
            m_ne = A_ne.getM()
        if A_ee is not None and A_ee.getC()>0 and (self.findNearSegment(A_ee,p,t) is None):
            m_ee = A_ee.getM()
        if A_se is not None and A_se.getC()>0 and (self.findNearSegment(A_se,p,t) is None):
            m_se = A_se.getM()
        if A_ss is not None and A_ss.getC()>0 and (self.findNearSegment(A_ss,p,t) is None):
            m_ss = A_ss.getM()
        if A_sw is not None and A_sw.getC()>0 and (self.findNearSegment(A_sw,p,t) is None):
            m_sw = A_sw.getM()
        if A_ww is not None and A_ww.getC()>0 and (self.findNearSegment(A_ww,p,t) is None):
            m_ww = A_ww.getM()
        
        print("m_nw: %f,m_nn: %f,m_ne: %f,m_ee: %f,m_se: %f,m_ss: %f,m_sw: %f,,m_ww: %f\n" % (m_nw,m_nn,m_ne,m_ee,m_se,m_ss,m_sw,m_ww))
                    
                    
                    
        return [m_nw,m_nn,m_ne,m_ee,m_se,m_ss,m_sw,m_ww]


    def findSegment(self, i,j):
        key = "A"+"_"+str(j)+"_"+str(i)
        print("*****Id: %s, i: %i, j: %i" % (key,i,j))
        #for s in self.segments["segments"]:
        #    segment = s["obj"]
        #    print("Id: %s, X: %i, Y: %i" % (segment.getId(),segment.getPosX(),segment.getPosY()))
        #    if segment.getPosX()==i and segment.getPosY()==j:
        #        print(segment.getId())
        
        value = [d for d in self.segments["segments"] if d["key"]==key]
        #value = filter(lambda s: s[0] == key, self.segments["segments"])
        #print(len(value))
        if len(value)>0:
            return value[0]["obj"]
        else:
            return None

    def findNearSegment(self,test_segment,p,t):
        found_segment = None
        for s in self.sensors["sensors"]:
            path = s.getPath(p)
            found_segment = path.findSegmentwithT(test_segment,t)
            if found_segment is not None:
                return found_segment
            
    def tab1UI(self):
        layout = QFormLayout()
        dimension = QHBoxLayout()
        self.dimensionW = QSpinBox()
        self.dimensionW.setRange(10,100)
        self.dimensionH = QSpinBox()
        self.dimensionH.setRange(10,200)
        WLabel = QLabel("Width")
        HLabel = QLabel("Height")
        dimension.addWidget(WLabel)
        dimension.addWidget(self.dimensionW)
        dimension.addWidget(HLabel)
        dimension.addWidget(self.dimensionH)
        setbutton = QPushButton("Draw Region")
        setbutton.clicked.connect(self.drawGrid)

        assignGridVal = QHBoxLayout()
        assignRandom = QPushButton("Random")
        assignRandom.clicked.connect(self.genRandomGridVal)
        assignManual = QPushButton("Manual")
        #difLoad.clicked.connect(self.loadDifficulty)
        assignManual.clicked.connect(self.openAssignmentDialog)
       
        assignGridVal.addWidget(assignRandom)
        assignGridVal.addWidget(assignManual)

        #changeViewLayOut = QHBoxLayout()
        #noneView = QRadioButton("None")
        #noneView.toggled.connect(lambda:self.displayShade(0))
        #noneView.setChecked(True)
        #difView = QRadioButton("Difficulty")
        #difView.toggled.connect(lambda:self.displayShade(1))
        #detView = QRadioButton("Detectability")
        #detView.toggled.connect(lambda:self.displayShade(2))
        #statView = QRadioButton("Statistic")
        #statView.toggled.connect(lambda:self.displayShade(3))
        #mView = QRadioButton("Significant")
        #mView.toggled.connect(lambda:self.displayShade(4))
        #changeView.addWidget(noneView)
        #changeView.addWidget(difView)
        #changeView.addWidget(detView)
        #changeView.addWidget(statView)
        #changeView.addWidget(mView)
        changeView = QComboBox()
        changeView.addItem("None")
        changeView.addItem("Difficulty")
        changeView.addItem("Obscurity")
        changeView.addItem("Statistic")
        changeView.currentIndexChanged.connect(self.displayShade)
        #changeViewLayOut.addWidget(changeView)

        self.weightC = QDoubleSpinBox()
        self.weightC.setRange(0.00,100.00)
        self.weightC.setSingleStep(0.01)
        self.weightC.setDecimals(2)
        self.weightC.setValue(1.00)

        self.weightO = QDoubleSpinBox()
        self.weightO.setRange(0.00,100.00)
        self.weightO.setSingleStep(0.01)
        self.weightO.setDecimals(2)
        self.weightO.setValue(1.00)

        self.weightS = QDoubleSpinBox()
        self.weightS.setRange(0.00,100.00)
        self.weightS.setSingleStep(0.01)
        self.weightS.setDecimals(2)
        self.weightS.setValue(1.00)

        self.weightH = QDoubleSpinBox()
        self.weightH.setRange(0.00,100.00)
        self.weightH.setSingleStep(0.01)
        self.weightH.setDecimals(2)
        self.weightH.setValue(1.00)

        weightParams1 = QHBoxLayout()
        weightParams1.addWidget(QLabel("Ease of pass Weight:"))
        weightParams1.addWidget(self.weightC)
        weightParams1.addWidget(QLabel("Obscurity Weight:"))
        weightParams1.addWidget(self.weightO)

        weightParams2 = QHBoxLayout()
        weightParams2.addWidget(QLabel("Statistic Weight:"))
        weightParams2.addWidget(self.weightS)
        weightParams2.addWidget(QLabel("Relative distance Weight:"))
        weightParams2.addWidget(self.weightH)

        

        
       
        
        calMButton = QPushButton("Calculate Significant Level")
        calMButton.clicked.connect(self.calculateMLevel)
        
        self.numberSensorsInput = QSpinBox()
        self.numberSensorsInput.setRange(1,500)
        self.coverageRadius = QSpinBox()
        self.coverageRadius.setRange(0,10)
        
        #movementSchemes = QHBoxLayout()
        #self.movementSchemeRandom = QRadioButton("Random")
    #self.movementSchemeRandom.toggled.connect(lambda:self.setMovementSchema(self.movementSchemeRandom))
        #self.movementSchemeRandom.setChecked(True)
        #movementSchemes.addWidget(self.movementSchemeRandom)
        #self.movementSchemeSimple = QRadioButton("Simple")
    #self.movementSchemeSimple.toggled.connect(lambda:self.setMovementSchema(self.movementSchemeSimple))
        #movementSchemes.addWidget(self.movementSchemeSimple)
        #self.movementSchemeSig = QRadioButton("Significant-based")
        #self.movementSchemeSig.toggled.connect(lambda:self.setMovementSchema(self.movementSchemeSig))
        #movementSchemes.addWidget(self.movementSchemeSig)
        #movementSchemes.addStretch(1)
        #movementGroupBox = QGroupBox("Non-Exclusive Checkboxes")
        #movementGroupBox.setLayout(movementSchemes)
        
        movementSchemes = QComboBox()
        movementSchemes.addItem("Stationary")
        movementSchemes.addItem("Random")
        movementSchemes.addItem("Single Barrier")
        movementSchemes.addItem("Double Barrier")
        movementSchemes.addItem("Significant-based")
        movementSchemes.currentIndexChanged.connect(self.setMovementSchema)
        
        sensorSchemes = QComboBox()
        sensorSchemes.addItem("Random")
        sensorSchemes.addItem("Manual")
        sensorSchemes.currentIndexChanged.connect(self.setSensorSchema)

        sensorModels = QComboBox()
        sensorModels.addItem("Ideal")
        sensorModels.addItem("Realistic")
        sensorModels.currentIndexChanged.connect(self.setSensorModel)
        
        setSensorButton = QPushButton("Place Sensors")
        setSensorButton.clicked.connect(self.placeSensors)
        
        self.stageDuration = QDoubleSpinBox()
        self.stageDuration.setRange(0.00,100.00)
        self.stageDuration.setSingleStep(0.1)
        self.stageDuration.setValue(1)
        self.numberStages = QSpinBox()
        self.numberStages.setRange(0,1000)
        self.numberStages.setSingleStep(10)
        self.numberStages.setValue(10)
        self.numberPeriods = QSpinBox()
        self.numberPeriods.setRange(0,100)
        self.numberPeriods.setSingleStep(1)
        self.numberPeriods.setValue(1)
        
        intruderArrSchemes = QHBoxLayout()
        self.intruderPoissonArr = QRadioButton("Poisson")
        self.intruderPoissonArr.setChecked(True)
        self.intruderParetoArr = QRadioButton("Deterministic")
        intruderArrSchemes.addWidget(self.intruderPoissonArr)
        intruderArrSchemes.addWidget(self.intruderParetoArr)
        
        self.intruderAvgArrRate1 = QSpinBox()
        self.intruderAvgArrRate1.setRange(0,100)
        self.intruderAvgArrRate1.setSingleStep(1)
        self.intruderAvgArrRate1.setValue(1)
        self.intruderAvgArrRate2 = QSpinBox()
        self.intruderAvgArrRate2.setRange(0,100)
        self.intruderAvgArrRate2.setSingleStep(1)
        self.intruderAvgArrRate2.setValue(1)
        self.trespmovementSchemes = QComboBox()
        self.trespmovementSchemes.addItem("Random")
        self.trespmovementSchemes.addItem("By Environment")
        #trespmovementSchemes.currentIndexChanged.connect(self.setMovementSchema)
        self.trespActiveTime = QSpinBox()
        self.trespActiveTime.setRange(0,100)
        self.trespActiveTime.setSingleStep(1)
        self.trespActiveTime.setValue(1)

        simcontrol = QHBoxLayout()
        calpathButton = QPushButton("Calculate Path")
        calpathButton.clicked.connect(self.calculatePath)
        runButton = QPushButton("Run Simulation")
        runButton.clicked.connect(self.startTimer)
        stopButton = QPushButton("Stop Simulation")
        stopButton.clicked.connect(self.stopTimer)
        simcontrol.addWidget(calpathButton)
        simcontrol.addWidget(runButton)
        simcontrol.addWidget(stopButton)
        
        layout.addRow("Region Dimension:",dimension)
        layout.addRow(setbutton)
        layout.addRow("Assign segment parameters:",assignGridVal)
        layout.addRow("Change region view:",changeView)
        layout.addRow(weightParams1)
        layout.addRow(weightParams2)
        #layout.addRow("Ease of pass Weight:",self.weightC)
        #layout.addRow("Obscurity Weight:",self.weightO)
        #layout.addRow("Statistic Weight:",self.weightS)
        #layout.addRow("Relative position Weight:",self.weightH)
        #layout.addRow("Likelihood Weight:",self.weightH)
        layout.addRow(calMButton)
        layout.addRow("Number of Sensors:",self.numberSensorsInput)

        layout.addRow("Coverage Radius:",self.coverageRadius)
        layout.addRow("Movement Scheme:",movementSchemes)
        layout.addRow("Placing Scheme:",sensorSchemes)
        layout.addRow(setSensorButton)
        layout.addRow("Intruder Arrival Model:",intruderArrSchemes)
        layout.addRow("Avg. Intruder Arrivals in a period:",self.intruderAvgArrRate1)
        layout.addRow("Avg. Normal trespasser Arrivals in a period:",self.intruderAvgArrRate2)
        layout.addRow("Trespasser movement:",self.trespmovementSchemes)
        layout.addRow("Trespasser is active after:",self.trespActiveTime)
        layout.addRow("Stage Duration:",self.stageDuration)
        layout.addRow("Number of stages in a period",self.numberStages)
        layout.addRow("Number of periods to simulate",self.numberPeriods)
        self.print_curT = QLabel(str(0))
        layout.addRow("Current time stage:",self.print_curT)
        self.print_curP = QLabel(str(0))
        layout.addRow("Current period:",self.print_curP)
        self.print_curTP = QLabel(str(0))
        layout.addRow("Current time stage in the period:",self.print_curTP)
        layout.addRow(simcontrol)
        self.tabView.setTabText(0,"Simulation Parameters")
        self.tab1.setLayout(layout)

    def tab2UI(self):
        layout = QFormLayout()
        self.tabView.setTabText(1,"Simulation Results")
        self.tab2.setLayout(layout)
        
        self.printNum_ientry = QLabel(str(0))
        layout.addRow("number of intruder entering the region:",self.printNum_ientry)
        self.printNum_iexit = QLabel(str(0))
        layout.addRow("number of intruder exiting the region:",self.printNum_iexit)
        self.printNum_idetected = QLabel(str(0))
        layout.addRow("number of intruder detected the region:",self.printNum_idetected)
        self.printNum_tentry = QLabel(str(0))
        layout.addRow("number of normal trespasser entering the region:",self.printNum_tentry)
        self.printNum_texit = QLabel(str(0))
        layout.addRow("number of normal trespasser exiting the region:",self.printNum_texit)
        self.printNum_tdetected = QLabel(str(0))
        layout.addRow("number of normal trespasser detected the region:",self.printNum_tdetected)

    def startTimer(self):
        for s in self.sensors["sensors"]:
            startA = s.getStartLoc()
            s.setCurrentLoc(startA)
            s_node = s.getNode()
            s_node.setPos(0,0)
        self.curT = 0
        self.cintruders = {"intruders":[]}
        self.nintruders = {"intruders":[]}
        self.generateIntruders(1)
        step = self.stageDuration.value()*1000
        self.timer.start(step)

    def stopTimer(self):
        
        self.number_ientry = 0    #number of intruder entering the area during the period
        self.number_tentry = 0    #number of regular trespasser entering the area during the period
        self.number_iexit_a = 0   #number of intruder exiting the area through the exit line
        self.number_texit_a = 0   #number of intruder exiting the area through the sides
        self.number_idetected = 0 #number of intruder detected by a sensors (true detection)
        self.number_tdetected = 0 #number of intruder detected by a sensors (false detection)
        self.printNum_ientry.setText(str(0))
        self.printNum_iexit.setText(str(0))
        self.printNum_idetected.setText(str(0))
        self.printNum_tentry.setText(str(0))
        self.printNum_texit.setText(str(0))
        self.printNum_tdetected.setText(str(0))
        for s in self.sensors["sensors"]:
            s_node = s.getNode()
            s_node.setPos(0,0)
        for k in self.cintruders["intruders"]:
            k_node = k.getNode()
            if k_node is not None:
                self.scene.removeItem(k_node)

        for k in self.nintruders["intruders"]:
            k_node = k.getNode()
            if k_node is not None:
                self.scene.removeItem(k_node)

        
        self.curT = 0
        self.timer.stop()

    def doSimulation(self):
        
        
        self.curT = self.curT + 1                   #aggregated current time stage
        stages = self.numberStages.value()
        t = np.mod(self.curT, stages)               #current time stage in a period
        p = np.ceil(np.divide(self.curT, stages))   #current period
        #t_s = np.mod(self.curT, stages)
        self.print_curT.setText(str(self.curT))
        self.print_curP.setText(str(p))
        self.print_curTP.setText(str(t))
        if t==0:   #at the beginning of a period, remove trespassser from previous periods, determine time of arrival of each trespasser
            if p<self.numberPeriods.value():
                self.generateIntruders(p+1)
            t = stages
        if p<=self.numberPeriods.value():
            i = 1
            for s in self.sensors["sensors"]:
                curA = s.getCurrentLoc()
                curX = curA.getPosX()
                curY = curA.getPosY()
                s_path = s.getPath(p)
                nextA = s_path.getSegment(t)
                nextX = nextA.getPosX()
                nextY = nextA.getPosY()
                s_node = s.getNode()
                s_point = s_node.pos()
                print("current coordinate ix: %f iy: %f x: %f y:%f" % (curX, curY, s_point.x(),s_point.y()))
                print("next coordinate ix: %f iy: %f x: %f y: %f" % (nextX,nextY,s_point.x()+(nextX-curX)*self.grid_width,s_point.y()+(nextY-curY)*self.grid_width))
                s_nextpoint = QPointF(s_point.x()+(nextX-curX)*self.grid_width,s_point.y()+(nextY-curY)*self.grid_width)
                s_node.setPos(s_point.x()+(nextX-curX)*self.grid_width,s_point.y()+(nextY-curY)*self.grid_width)
                s.setCurrentLoc(nextA)
                s.setX(nextX)
                s.setY(nextY)
                print("Sensor %i in %s at %i" % (i,nextA.getId(),self.curT))
                i = i + 1

            for k in self.cintruders["intruders"]:
                #print("intruder %i arrive at %i" % (k.getId(),k.getArrTime()))
                if (int(k.getArrTime())==t and int(k.getPeriod())==p):
                    #print("Entry length: %i %i" % (len(self.entry_segments),len(self.entry_prob)))
                    if t>self.trespActiveTime.value():
                        self.number_ientry += 1
                        self.printNum_ientry.setText(str(self.number_ientry))
                    e_prob = []
                    total_we = 0
                    for i in range(0,self.number_h):
                        key = "A_"+str(i+1)+"_1"
                        w = self.findWeight(key,1)
                        total_we = total_we + w
                        #print("Entry segment %i prob %f" % (i+1,w))
                        e_prob.append(w)
                    
                    #e_prob = [0.048117, 0.066998, 0.076118, 0.088737, 0.026079, 0.143142, 0.137958, 0.12558, 0.126847, 0.160424]
                    #self.entry_prob
                    #np.reshape(e_prob,len(e_prob))
                    #e_prob = np.array(self.entry_prob)
                    #np.reshape(np.array(e_prob),len(e_prob))
                    e_arr = np.array(np.divide(e_prob,total_we))
                    
                    e_idx = np.random.choice(range(1,self.number_h+1),1,p=e_arr.flatten())
                    print("Intruder %i enter %i at %i" % (k.getId(),e_idx,t))
                    A_e = self.findSegment(1,e_idx[0])
                    AeX = A_e.getPosX()
                    AeY = A_e.getPosY()
                    node = self.scene.addEllipse(self.pos_x+(AeX-1)*self.grid_width,self.pos_y+(AeY-1)*self.grid_width,self.grid_width,self.grid_width,QColor(255,0,0,255),QColor(255,0,0,255))
                    node.setToolTip("Intruder %i at %s" % (k.getId(),A_e.getId()))
                    #print("crossing intruder %i enter %s at %i" % (k.getId(),A_e.getId(),t))
                    k.setNode(node)
                    k.setCurrentLoc(A_e)
                    k.moveInside()
                elif k.isInside()==1:
                    curA = k.getCurrentLoc()
                    curX = curA.getPosX()
                    curY = curA.getPosY()
                    
                    #set mobility here
                    
                    A_nw = None
                    A_nn = None
                    A_ne = None
                    A_ee = None
                    A_se = None
                    A_ss = None
                    A_sw = None
                    A_ww = None
                    
                    if curX>1 and curX<self.number_w and curY>1 and curY<self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==1 and curY==1:
                        A_nw = segmentObj(0,0,0,0,0,0,None)
                        A_nn = segmentObj(-1,0,0,0,0,0,None)
                        A_ne = segmentObj(-1,0,0,0,0,0,None)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = segmentObj(0,0,0,0,0,0,None)
                        A_ww = segmentObj(0,0,0,0,0,0,None)
                    elif curX>1 and curX<self.number_w and curY==1:
                        A_nw = segmentObj(-1,0,0,0,0,0,None)
                        A_nn = segmentObj(-1,0,0,0,0,0,None)
                        A_ne = segmentObj(-1,0,0,0,0,0,None)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==self.number_w and curY==1:
                        A_nw = segmentObj(-1,0,0,0,0,0,None)
                        A_nn = segmentObj(-1,0,0,0,0,0,None)
                        A_ne = segmentObj(-1,-1,0,0,0,0,None)
                        A_ee = segmentObj(-1,-1,0,0,0,0,None)
                        A_se = segmentObj(-1,-1,0,0,0,0,None)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==self.number_w and curY>1 and curY<self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = segmentObj(-1,-1,0,0,0,0,None)
                        A_ee = segmentObj(-1,-1,0,0,0,0,None)
                        A_se = segmentObj(-1,-1,0,0,0,0,None)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==self.number_w and curY==self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = segmentObj(-1,-1,0,0,0,0,None)
                        A_ee = segmentObj(-1,-1,0,0,0,0,None)
                        A_se = segmentObj(-1,-1,0,0,0,0,None)
                        A_ss = segmentObj(0,-1,0,0,0,0,None)
                        A_sw = segmentObj(0,-1,0,0,0,0,None)
                        A_ww = self.findSegment(curX-1,curY) 
                    elif curX>1 and curX<self.number_w and curY==self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = segmentObj(0,-1,0,0,0,0,None)
                        A_ss = segmentObj(0,-1,0,0,0,0,None)
                        A_sw = segmentObj(0,-1,0,0,0,0,None)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==1 and curY==self.number_h:
                        A_nw = segmentObj(0,0,0,0,0,0,None)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = segmentObj(0,-1,0,0,0,0,None)
                        A_ss = segmentObj(0,-1,0,0,0,0,None)
                        A_sw = segmentObj(0,0,0,0,0,0,None)
                        A_ww = segmentObj(0,0,0,0,0,0,None)
                    elif curX==1 and curY>1 and curY<self.number_h:
                        A_nw = segmentObj(0,0,0,0,0,0,None)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = segmentObj(0,0,0,0,0,0,None)
                        A_ww = segmentObj(0,0,0,0,0,0,None)

                    m_nw = 0
                    m_nn = 0
                    m_ne = 0
                    m_ee = 0
                    m_se = 0
                    m_ss = 0
                    m_sw = 0
                    m_ww = 0
                    w_exit_rate = 0
                    n_exit_rate = 0
                    e_exit_rate = 1
                    s_exit_rate = 0
                    if A_nw is not None:
                        if A_nw.getId()=='A_0_0':
                            m_nw = w_exit_rate
                        elif A_nw.getId()=='A_-1_0':
                            m_nw = n_exit_rate
                        elif A_nw.getId()=='A_-1_-1':
                            m_nw = e_exit_rate
                        elif A_nw.getId()=='A_0_-1':
                            m_nw = s_exit_rate
                        else:
                            #m_nw = A_nw.getM()
                            m_nw = self.findWeight(A_nw.getId(),1)
                    if A_nn is not None:
                        if A_nn.getId()=='A_0_0':
                            m_nn = w_exit_rate
                        elif A_nn.getId()=='A_-1_0':
                            m_nn = n_exit_rate
                        elif A_nn.getId()=='A_-1_-1':
                            m_nn = e_exit_rate
                        elif A_nn.getId()=='A_0_-1':
                            m_nn = s_exit_rate
                        else:
                            #m_nn = A_nn.getM()
                            m_nn = self.findWeight(A_nn.getId(),1)
                    if A_ne is not None:
                        if A_ne.getId()=='A_0_0':
                            m_ne = w_exit_rate
                        elif A_ne.getId()=='A_-1_0':
                            m_ne = n_exit_rate
                        elif A_ne.getId()=='A_-1_-1':
                            m_ne = e_exit_rate
                        elif A_ne.getId()=='A_0_-1':
                            m_ne = s_exit_rate
                        else:
                            #m_ne = A_ne.getM()
                            m_ne = self.findWeight(A_ne.getId(),1)
                    if A_ee is not None:
                        if A_ee.getId()=='A_0_0':
                            m_ee = w_exit_rate
                        elif A_ee.getId()=='A_-1_0':
                            m_ee = n_exit_rate
                        elif A_ee.getId()=='A_-1_-1':
                            m_ee = e_exit_rate
                        elif A_ee.getId()=='A_0_-1':
                            m_ee = s_exit_rate
                        else:
                            #m_ee = A_ee.getM()
                            m_ee = self.findWeight(A_ee.getId(),1)
                    if A_se is not None:
                        if A_se.getId()=='A_0_0':
                            m_se = w_exit_rate
                        elif A_se.getId()=='A_-1_0':
                            m_se = n_exit_rate
                        elif A_se.getId()=='A_-1_-1':
                            m_se = e_exit_rate
                        elif A_se.getId()=='A_0_-1':
                            m_se = s_exit_rate
                        else:
                            #m_se = A_se.getM()
                            m_se = self.findWeight(A_se.getId(),1)
                    if A_ss is not None:
                        if A_ss.getId()=='A_0_0':
                            m_ss = w_exit_rate
                        elif A_ss.getId()=='A_-1_0':
                            m_ss = n_exit_rate
                        elif A_ss.getId()=='A_-1_-1':
                            m_ss = e_exit_rate
                        elif A_ss.getId()=='A_0_-1':
                            m_ss = s_exit_rate
                        else:
                            #m_ss = A_ss.getM()
                            m_ss = self.findWeight(A_ss.getId(),1)
                    if A_sw is not None:
                        if A_sw.getId()=='A_0_0':
                            m_sw = w_exit_rate
                        elif A_sw.getId()=='A_-1_0':
                            m_sw = n_exit_rate
                        elif A_sw.getId()=='A_-1_-1':
                            m_sw = e_exit_rate
                        elif A_sw.getId()=='A_0_-1':
                            m_sw = s_exit_rate
                        else:
                            #m_sw = A_sw.getM()
                            m_sw = self.findWeight(A_sw.getId(),1)
                    if A_ww is not None:
                        if A_ww.getId()=='A_0_0':
                            m_ww = w_exit_rate
                        elif A_ww.getId()=='A_-1_0':
                            m_ww = n_exit_rate
                        elif A_ww.getId()=='A_-1_-1':
                            m_ww = e_exit_rate
                        elif A_ww.getId()=='A_0_-1':
                            m_ww = s_exit_rate
                        else:
                            #m_ww = A_ww.getM()
                            m_ww = self.findWeight(A_ww.getId(),1)

                    next_arr = [1,2,3,4,5,6,7,8]
                    #next_prob = [0.05, 0.1, 0.2, 0.2, 0.2, 0.1, 0.1, 0.05]
                    w_h = self.weightH.value()
                    m_nw = m_nw + w_h*self.weightRoute(curA.getId(),A_nw.getId(),1)
                    m_nn = m_nn + w_h*self.weightRoute(curA.getId(),A_nn.getId(),1)
                    m_ne = m_ne + w_h*self.weightRoute(curA.getId(),A_ne.getId(),1)
                    m_ee = m_ee + w_h*self.weightRoute(curA.getId(),A_ee.getId(),1)
                    m_se = m_se + w_h*self.weightRoute(curA.getId(),A_se.getId(),1)
                    m_ss = m_ss + w_h*self.weightRoute(curA.getId(),A_ss.getId(),1)
                    m_sw = m_sw + w_h*self.weightRoute(curA.getId(),A_sw.getId(),1)
                    m_ww = m_ww + w_h*self.weightRoute(curA.getId(),A_ww.getId(),1)
                    #m_nn = m_nn+w_h* if m_nn>0.1 else m_nn
                    #m_ne = m_ne+w_h*0.5 if m_ne>0.1 else m_ne
                    #m_ee = m_ee+w_h*1 if m_ee>0 else m_ee
                    #m_se = m_se+w_h*0.5 if m_se>0.1 else m_se
                    #m_ss = m_ss+w_h*0.25 if m_ss>0 else 0
                    next_prob = [m_nw,m_nn,m_ne,m_ee,m_se,m_ss,m_sw,m_ww]
                    weightSum = np.sum(next_prob)
                    next_prob = np.divide(next_prob,weightSum)
                    next_idx = np.random.choice(next_arr,1,p=next_prob)
                    nextA = None
                    if next_idx==1:
                        #nextA = self.findSegment(curX-1,curY-1)
                        nextA = A_nw
                    elif next_idx==2:
                        #nextA = self.findSegment(curX,curY-1)
                        nextA = A_nn
                    elif next_idx==3:
                        #nextA = self.findSegment(curX+1,curY-1)
                        nextA = A_ne
                    elif next_idx==4:
                        #nextA = self.findSegment(curX+1,curY)
                        nextA = A_ee
                    elif next_idx==5:
                        #nextA = self.findSegment(curX+1,curY+1)
                        nextA = A_se
                    elif next_idx==6:
                        #nextA = self.findSegment(curX,curY+1)
                        nextA = A_ss
                    elif next_idx==7:
                        #nextA = self.findSegment(curX-1,curY+1)
                        nextA = A_sw
                    elif next_idx==8:
                        #nextA = self.findSegment(curX-1,curY)
                        nextA = A_ww
                    #check for detection
                    for s in self.sensors["sensors"]:
                        sensorA = s.getCurrentLoc()
                        sensorX = sensorA.getPosX()
                        sensorY = sensorA.getPosY()
                        intruderX = nextA.getPosX()
                        intruderY = nextA.getPosY()
                        if t>self.trespActiveTime.value() and np.absolute(intruderX-sensorX)<=self.coverageRadius.value() and np.absolute(intruderY-sensorY)<=self.coverageRadius.value():
                            nextA = segmentObj('x','x',0,0,0,0,None)
                            break
                    
                    if nextA is not None and nextA.getId()!='A_0_0' and nextA.getId()!='A_-1_0' and nextA.getId()!='A_0_-1' and nextA.getId()!='A_-1_-1' and nextA.getId()!='A_x_x':
                        
                        #nextA = s_path.getSegment(t)
                        nextX = nextA.getPosX()
                        nextY = nextA.getPosY()
                        k_node = k.getNode()
                        k_point = k_node.pos()
                        #print("current coordinate ix: %f iy: %f x: %f y:%f" % (curX, curY, s_point.x(),s_point.y()))
                        #print("next coordinate ix: %f iy: %f x: %f y: %f" % (nextX,nextY,s_point.x()+(nextX-curX)*self.grid_width,s_point.y()+(nextY-curY)*self.grid_width))
                        k_nextpoint = QPointF(k_point.x()+(nextX-curX)*self.grid_width,k_point.y()+(nextY-curY)*self.grid_width)
                        k_node.setPos(k_point.x()+(nextX-curX)*self.grid_width,k_point.y()+(nextY-curY)*self.grid_width)
                    elif nextA.getId()=='A_x_x':
                        self.number_idetected += 1
                        self.printNum_idetected.setText(str(self.number_idetected))
                        k_node = k.getNode()
                        self.scene.removeItem(k_node)
                        k.isDetected()
                    # else:
                    #     k_node = k.getNode()
                    #     self.scene.removeItem(k_node)
                    #     self.number_iexit_a += 1
                    #     self.printNum_iexit.setText(str(self.number_iexit_a))
                    #     k.moveOutside()    
                    else:
                        k_node = k.getNode()
                        self.scene.removeItem(k_node)
                        if t>self.trespActiveTime.value():
                            self.number_iexit_a += 1
                            self.printNum_iexit.setText(str(self.number_iexit_a))
                        k.moveOutside()
                    
                    k.setCurrentLoc(nextA)

            for k in self.nintruders["intruders"]:
                #print("intruder %i arrive at %i" % (k.getId(),k.getArrTime()))
                if (int(k.getArrTime())==t and int(k.getPeriod())==p):
                    #print("Entry length: %i %i" % (len(self.entry_segments),len(self.entry_prob)))
                    if t>self.trespActiveTime.value():
                        self.number_tentry += 1
                        self.printNum_tentry.setText(str(self.number_ientry))
                    e_prob = []
                    total_we = 0
                    for i in range(0,self.number_h):
                        key = "A_"+str(i+1)+"_1"
                        w = self.findWeight(key,2)
                        total_we = total_we + w
                        #print("Entry segment %i prob %f" % (i+1,w))
                        e_prob.append(w)
                    
                    #e_prob = [0.048117, 0.066998, 0.076118, 0.088737, 0.026079, 0.143142, 0.137958, 0.12558, 0.126847, 0.160424]
                    #self.entry_prob
                    #np.reshape(e_prob,len(e_prob))
                    #e_prob = np.array(self.entry_prob)
                    #np.reshape(np.array(e_prob),len(e_prob))
                    e_arr = np.array(np.divide(e_prob,total_we))
                    
                    e_idx = np.random.choice(range(1,self.number_h+1),1,p=e_arr.flatten())
                    print("Normal trespasser %i enter %i at %i" % (k.getId(),e_idx,t))
                    A_e = self.findSegment(1,e_idx[0])
                    AeX = A_e.getPosX()
                    AeY = A_e.getPosY()
                    node = self.scene.addEllipse(self.pos_x+(AeX-1)*self.grid_width,self.pos_y+(AeY-1)*self.grid_width,self.grid_width,self.grid_width,QColor(255,127,0,255),QColor(255,127,0,255))
                    node.setToolTip("Normal trespasser %i at %s" % (k.getId(),A_e.getId()))
                    #print("crossing intruder %i enter %s at %i" % (k.getId(),A_e.getId(),t))
                    k.setNode(node)
                    k.setCurrentLoc(A_e)
                    k.moveInside()
                elif k.isInside()==1:
                    curA = k.getCurrentLoc()
                    curX = curA.getPosX()
                    curY = curA.getPosY()
                    
                    #set mobility here
                    
                    A_nw = None
                    A_nn = None
                    A_ne = None
                    A_ee = None
                    A_se = None
                    A_ss = None
                    A_sw = None
                    A_ww = None
                    
                    if curX>1 and curX<self.number_w and curY>1 and curY<self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==1 and curY==1:
                        A_nw = segmentObj(0,0,0,0,0,0,None)
                        A_nn = segmentObj(-1,0,0,0,0,0,None)
                        A_ne = segmentObj(-1,0,0,0,0,0,None)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = segmentObj(0,0,0,0,0,0,None)
                        A_ww = segmentObj(0,0,0,0,0,0,None)
                    elif curX>1 and curX<self.number_w and curY==1:
                        A_nw = segmentObj(-1,0,0,0,0,0,None)
                        A_nn = segmentObj(-1,0,0,0,0,0,None)
                        A_ne = segmentObj(-1,0,0,0,0,0,None)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==self.number_w and curY==1:
                        A_nw = segmentObj(-1,0,0,0,0,0,None)
                        A_nn = segmentObj(-1,0,0,0,0,0,None)
                        A_ne = segmentObj(-1,-1,0,0,0,0,None)
                        A_ee = segmentObj(-1,-1,0,0,0,0,None)
                        A_se = segmentObj(-1,-1,0,0,0,0,None)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==self.number_w and curY>1 and curY<self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = segmentObj(-1,-1,0,0,0,0,None)
                        A_ee = segmentObj(-1,-1,0,0,0,0,None)
                        A_se = segmentObj(-1,-1,0,0,0,0,None)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = self.findSegment(curX-1,curY+1)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==self.number_w and curY==self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = segmentObj(-1,-1,0,0,0,0,None)
                        A_ee = segmentObj(-1,-1,0,0,0,0,None)
                        A_se = segmentObj(-1,-1,0,0,0,0,None)
                        A_ss = segmentObj(0,-1,0,0,0,0,None)
                        A_sw = segmentObj(0,-1,0,0,0,0,None)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX>1 and curX<self.number_w and curY==self.number_h:
                        A_nw = self.findSegment(curX-1,curY-1)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = segmentObj(0,-1,0,0,0,0,None)
                        A_ss = segmentObj(0,-1,0,0,0,0,None)
                        A_sw = segmentObj(0,-1,0,0,0,0,None)
                        A_ww = self.findSegment(curX-1,curY)
                    elif curX==1 and curY==self.number_h:
                        A_nw = segmentObj(0,0,0,0,0,0,None)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = segmentObj(0,-1,0,0,0,0,None)
                        A_ss = segmentObj(0,-1,0,0,0,0,None)
                        A_sw = segmentObj(0,0,0,0,0,0,None)
                        A_ww = segmentObj(0,0,0,0,0,0,None)
                    elif curX==1 and curY>1 and curY<self.number_h:
                        A_nw = segmentObj(0,0,0,0,0,0,None)
                        A_nn = self.findSegment(curX,curY-1)
                        A_ne = self.findSegment(curX+1,curY-1)
                        A_ee = self.findSegment(curX+1,curY)
                        A_se = self.findSegment(curX+1,curY+1)
                        A_ss = self.findSegment(curX,curY+1)
                        A_sw = segmentObj(0,0,0,0,0,0,None)
                        A_ww = segmentObj(0,0,0,0,0,0,None)

                    m_nw = 0
                    m_nn = 0
                    m_ne = 0
                    m_ee = 0
                    m_se = 0
                    m_ss = 0
                    m_sw = 0
                    m_ww = 0
                    w_exit_rate = 1
                    n_exit_rate = 0
                    e_exit_rate = 0
                    s_exit_rate = 0
                    if A_nw is not None:
                        if A_nw.getId()=='A_0_0':
                            m_nw = w_exit_rate
                        elif A_nw.getId()=='A_-1_0':
                            m_nw = n_exit_rate
                        elif A_nw.getId()=='A_-1_-1':
                            m_nw = e_exit_rate
                        elif A_nw.getId()=='A_0_-1':
                            m_nw = s_exit_rate
                        else:
                            #m_nw = A_nw.getM()
                            m_nw = self.findWeight(A_nw.getId(),1)
                    if A_nn is not None:
                        if A_nn.getId()=='A_0_0':
                            m_nn = w_exit_rate
                        elif A_nn.getId()=='A_-1_0':
                            m_nn = n_exit_rate
                        elif A_nn.getId()=='A_-1_-1':
                            m_nn = e_exit_rate
                        elif A_nn.getId()=='A_0_-1':
                            m_nn = s_exit_rate
                        else:
                            #m_nn = A_nn.getM()
                            m_nn = self.findWeight(A_nn.getId(),1)
                    if A_ne is not None:
                        if A_ne.getId()=='A_0_0':
                            m_ne = w_exit_rate
                        elif A_ne.getId()=='A_-1_0':
                            m_ne = n_exit_rate
                        elif A_ne.getId()=='A_-1_-1':
                            m_ne = e_exit_rate
                        elif A_ne.getId()=='A_0_-1':
                            m_ne = s_exit_rate
                        else:
                            #m_ne = A_ne.getM()
                            m_ne = self.findWeight(A_ne.getId(),1)
                    if A_ee is not None:
                        if A_ee.getId()=='A_0_0':
                            m_ee = w_exit_rate
                        elif A_ee.getId()=='A_-1_0':
                            m_ee = n_exit_rate
                        elif A_ee.getId()=='A_-1_-1':
                            m_ee = e_exit_rate
                        elif A_ee.getId()=='A_0_-1':
                            m_ee = s_exit_rate
                        else:
                            #m_ee = A_ee.getM()
                            m_ee = self.findWeight(A_ee.getId(),1)
                    if A_se is not None:
                        if A_se.getId()=='A_0_0':
                            m_se = w_exit_rate
                        elif A_se.getId()=='A_-1_0':
                            m_se = n_exit_rate
                        elif A_se.getId()=='A_-1_-1':
                            m_se = e_exit_rate
                        elif A_se.getId()=='A_0_-1':
                            m_se = s_exit_rate
                        else:
                            #m_se = A_se.getM()
                            m_se = self.findWeight(A_se.getId(),1)
                    if A_ss is not None:
                        if A_ss.getId()=='A_0_0':
                            m_ss = w_exit_rate
                        elif A_ss.getId()=='A_-1_0':
                            m_ss = n_exit_rate
                        elif A_ss.getId()=='A_-1_-1':
                            m_ss = e_exit_rate
                        elif A_ss.getId()=='A_0_-1':
                            m_ss = s_exit_rate
                        else:
                            #m_ss = A_ss.getM()
                            m_ss = self.findWeight(A_ss.getId(),1)
                    if A_sw is not None:
                        if A_sw.getId()=='A_0_0':
                            m_sw = w_exit_rate
                        elif A_sw.getId()=='A_-1_0':
                            m_sw = n_exit_rate
                        elif A_sw.getId()=='A_-1_-1':
                            m_sw = e_exit_rate
                        elif A_sw.getId()=='A_0_-1':
                            m_sw = s_exit_rate
                        else:
                            #m_sw = A_sw.getM()
                            m_sw = self.findWeight(A_sw.getId(),1)
                    if A_ww is not None:
                        if A_ww.getId()=='A_0_0':
                            m_ww = w_exit_rate
                        elif A_ww.getId()=='A_-1_0':
                            m_ww = n_exit_rate
                        elif A_ww.getId()=='A_-1_-1':
                            m_ww = e_exit_rate
                        elif A_ww.getId()=='A_0_-1':
                            m_ww = s_exit_rate
                        else:
                            #m_ww = A_ww.getM()
                            m_ww = self.findWeight(A_ww.getId(),1)

                    next_arr = [1,2,3,4,5,6,7,8]
                    #next_prob = [0.05, 0.1, 0.2, 0.2, 0.2, 0.1, 0.1, 0.05]
                    w_h = self.weightH.value()
                    m_nw = m_nw + w_h*self.weightRoute(curA.getId(),A_nw.getId(),2)
                    m_nn = m_nn + w_h*self.weightRoute(curA.getId(),A_nn.getId(),2)
                    m_ne = m_ne + w_h*self.weightRoute(curA.getId(),A_ne.getId(),2)
                    m_ee = m_ee + w_h*self.weightRoute(curA.getId(),A_ee.getId(),2)
                    m_se = m_se + w_h*self.weightRoute(curA.getId(),A_se.getId(),2)
                    m_ss = m_ss + w_h*self.weightRoute(curA.getId(),A_ss.getId(),2)
                    m_sw = m_sw + w_h*self.weightRoute(curA.getId(),A_sw.getId(),2)
                    m_ww = m_ww + w_h*self.weightRoute(curA.getId(),A_ww.getId(),2)
                    #m_nn = m_nn+w_h* if m_nn>0.1 else m_nn
                    #m_ne = m_ne+w_h*0.5 if m_ne>0.1 else m_ne
                    #m_ee = m_ee+w_h*1 if m_ee>0 else m_ee
                    #m_se = m_se+w_h*0.5 if m_se>0.1 else m_se
                    #m_ss = m_ss+w_h*0.25 if m_ss>0 else 0
                    next_prob = [m_nw,m_nn,m_ne,m_ee,m_se,m_ss,m_sw,m_ww]
                    weightSum = np.sum(next_prob)
                    next_prob = np.divide(next_prob,weightSum)
                    next_idx = np.random.choice(next_arr,1,p=next_prob)
                    nextA = None
                    if next_idx==1:
                        #nextA = self.findSegment(curX-1,curY-1)
                        nextA = A_nw
                    elif next_idx==2:
                        #nextA = self.findSegment(curX,curY-1)
                        nextA = A_nn
                    elif next_idx==3:
                        #nextA = self.findSegment(curX+1,curY-1)
                        nextA = A_ne
                    elif next_idx==4:
                        #nextA = self.findSegment(curX+1,curY)
                        nextA = A_ee
                    elif next_idx==5:
                        #nextA = self.findSegment(curX+1,curY+1)
                        nextA = A_se
                    elif next_idx==6:
                        #nextA = self.findSegment(curX,curY+1)
                        nextA = A_ss
                    elif next_idx==7:
                        #nextA = self.findSegment(curX-1,curY+1)
                        nextA = A_sw
                    elif next_idx==8:
                        #nextA = self.findSegment(curX-1,curY)
                        nextA = A_ww

                    #check for detection
                    for s in self.sensors["sensors"]:
                        sensorA = s.getCurrentLoc()
                        sensorX = sensorA.getPosX()
                        sensorY = sensorA.getPosY()
                        intruderX = nextA.getPosX()
                        intruderY = nextA.getPosY()
                        if t>self.trespActiveTime.value() and np.absolute(intruderX-sensorX)<=self.coverageRadius.value() and np.absolute(intruderY-sensorY)<=self.coverageRadius.value():
                            nextA = segmentObj('x','x',0,0,0,0,None)
                            break

                    if nextA is not None and nextA.getId()!='A_0_0' and nextA.getId()!='A_-1_0' and nextA.getId()!='A_0_-1' and nextA.getId()!='A_-1_-1' and nextA.getId()!='A_x_x':
    
                        #nextA = s_path.getSegment(t)
                        nextX = nextA.getPosX()
                        nextY = nextA.getPosY()
                        k_node = k.getNode()
                        k_point = k_node.pos()
                        #print("current coordinate ix: %f iy: %f x: %f y:%f" % (curX, curY, s_point.x(),s_point.y()))
                        #print("next coordinate ix: %f iy: %f x: %f y: %f" % (nextX,nextY,s_point.x()+(nextX-curX)*self.grid_width,s_point.y()+(nextY-curY)*self.grid_width))
                        k_nextpoint = QPointF(k_point.x()+(nextX-curX)*self.grid_width,k_point.y()+(nextY-curY)*self.grid_width)
                        k_node.setPos(k_point.x()+(nextX-curX)*self.grid_width,k_point.y()+(nextY-curY)*self.grid_width)
                    elif nextA.getId()=='A_x_x':
                        self.number_tdetected += 1
                        self.printNum_tdetected.setText(str(self.number_tdetected))
                        k_node = k.getNode()
                        self.scene.removeItem(k_node)
                        k.isDetected()
                    else:
                        k_node = k.getNode()
                        self.scene.removeItem(k_node)
                        if t>self.trespActiveTime.value():
                            self.number_texit_a += 1
                            self.printNum_texit.setText(str(self.number_texit_a))
                        k.moveOutside()
                    
                    k.setCurrentLoc(nextA)

        if t==stages and p==self.numberPeriods.value():
            self.timer.stop()

    def weightRoute(self,curkey,key,type):
        cur_list = [d for d in self.segments["segments"] if d["key"]==curkey]
        cur_segment = cur_list[0]["obj"]
        curX = cur_segment.getPosX()
        curY = cur_segment.getPosY()
        if type==1:
            if key=='A_0_0':
                return 0
            elif key=='A_-1_0':
                return 0
            elif key=='A_-1_-1':
                return 10
            elif key=='A_0_-1':
                return 0
            else:
                e_list = [d for d in self.segments["segments"] if d["key"]==key]
                e_segment = e_list[0]["obj"]
                nextX = e_segment.getPosX()
                nextY = e_segment.getPosY()
                nextB = e_segment.getC()
                if nextB==0:
                    return 0
                if curX==nextX:
                    return 5
                elif curX<nextX and curY!=nextY:
                    return 50
                elif curX<nextX and curY==nextY:
                    return 75
                else:
                    return 0
        elif type==2:
            if key=='A_0_0':
                return 10
            elif key=='A_-1_0':
                return 0
            elif key=='A_-1_-1':
                return 0
            elif key=='A_0_-1':
                return 0
            else:
                e_list = [d for d in self.segments["segments"] if d["key"]==key]
                e_segment = e_list[0]["obj"]
                nextX = e_segment.getPosX()
                nextY = e_segment.getPosY()
                if curX<self.number_w*0.5:
                    return 25
                elif curX>=self.number_w*0.5 and curX>nextX:
                    return 75
                elif curX>=self.number_w*0.5 and curX<=nextX:
                    return 2
                else:
                    return 0
    def findWeight(self,key,type):
         #calculate prob of entry_segments
        #total_e = 0
        #e_prob = []
        #for i in self.entry_segments:
        #    key = "A_"+str(i)+"_1"
        e_list = [d for d in self.segments["segments"] if d["key"]==key]
        e_segment = e_list[0]["obj"]
        c = e_segment.getC()
        o = e_segment.getO()
        s = e_segment.getS()
        #h = e_segment.getH()
        if c==0:
            return 0
        w_c = self.weightC.value()
        w_o = self.weightO.value()
        w_s = self.weightS.value()
        #w_h = self.weightH.value()
        if type==1:
            s_max = max(self.segments["segments"], key=lambda x:x["obj"].getS())
            s_min = min(self.segments["segments"], key=lambda x:x["obj"].getS())
            if s_max["obj"].getS()>s_min["obj"].getS():
                return w_c*c+w_o*(1-o)+w_s*(s-s_min["obj"].getS())/(s_max["obj"].getS()-s_min["obj"].getS())    #+w_h*h
            else:
                return w_c*c+w_o*(1-o)  #+w_h*h
        else:
            return w_c*c
        #    total_e = total_e+e
        #    e_prob.append(e)

        #self.entry_prob = np.divide(e_prob,total_e)
        
    def generateIntruders(self, period):
        if self.intruderPoissonArr.isChecked():
            arr_model = "Poisson"
        else:
            arr_model = "Deterministic"

        print("Arrival model: %s" % arr_model)    
        lambda1 = self.intruderAvgArrRate1.value()
        lambda2 = self.intruderAvgArrRate2.value()
        stages = self.numberStages.value()
        if arr_model=="Poisson":
            n1 = np.random.poisson(lambda1)
            n2 = np.random.poisson(lambda2)
        else:
            n1 = lambda1
            n2 = lambda2
        print("#arrivals in period %i c: %i n: %i" % (period, n1, n2)) 
        arr_time =0
        for i in range(0,n1):
            if arr_model=="Poisson":
                arr_time = np.floor(np.random.uniform(1,stages))
            else:
                arr_time = arr_time+np.floor(stages/n1)
            intruder = intruderObj(i+1,1,arr_time,period)
            self.cintruders["intruders"].append(intruder)

        for j in range(0,n2):
            if arr_model=="Poisson":
                arr_time = np.floor(np.random.uniform(1,stages))
            else:
                arr_time = arr_time+np.floor(stages/n1)
            intruder = intruderObj(j+1,2,arr_time,period)
            self.nintruders["intruders"].append(intruder)


    def openAssignmentDialog(self):
        assignDialog = QDialog()
        assignLayout = QFormLayout(assignDialog)
        tabView = QTabWidget()
        tab1 = QWidget()
        tab2 = QWidget()
        tab3 = QWidget()
        tab1Layout = QFormLayout(tab1)
        d = 0
        rowC = [None]*self.number_h
        self.segC = [None]*self.number_h*self.number_w
        for j in range(0,self.number_h):
            rowC[j] = QHBoxLayout() 
            for i in range(0,self.number_w):
                s = self.segments["segments"][d]["obj"]
                
                #print("C %f" % s.getC())
                self.segC[d] = QDoubleSpinBox()
                self.segC[d].setRange(0.000000,1.000000)
                self.segC[d].setSingleStep(0.1)
                self.segC[d].setDecimals(6)
                self.segC[d].setValue(s.getC())
                self.segC[d].valueChanged.connect(partial(self.recordSegmentCParameter,d=d))
                rowC[j].addWidget(self.segC[d])
                d = d + 1
            tab1Layout.addRow(rowC[j])

        loadbtn1 = QPushButton("Load from file")
        loadbtn1.clicked.connect(self.openBFileDialog)
        tab1Layout.addRow(loadbtn1)
        
    
        tab2Layout = QFormLayout(tab2)
        d = 0
        rowO = [None]*self.number_h
        self.segO = [None]*self.number_h*self.number_w
        for j in range(0,self.number_h):
            rowO[j] = QHBoxLayout() 
            for i in range(0,self.number_w):
                s = self.segments["segments"][d]["obj"]
                
                #print("C %f" % s.getC())
                self.segO[d] = QDoubleSpinBox()
                self.segO[d].setRange(0.00,100.00)
                self.segO[d].setSingleStep(0.1)
                self.segO[d].setValue(s.getO())
                self.segO[d].valueChanged.connect(partial(self.recordSegmentOParameter,d=d))
                rowO[j].addWidget(self.segO[d])
                d = d + 1
            tab2Layout.addRow(rowO[j])

        loadbtn2 = QPushButton("Load from file")
        loadbtn2.clicked.connect(self.openOFileDialog)
        tab2Layout.addRow(loadbtn2)

        tab3Layout = QFormLayout(tab3)
        d = 0
        rowS = [None]*self.number_h
        self.segS = [None]*self.number_h*self.number_w
        for j in range(0,self.number_h):
            rowS[j] = QHBoxLayout() 
            for i in range(0,self.number_w):
                s = self.segments["segments"][d]["obj"]
                
                #print("C %f" % s.getC())
                self.segS[d] = QDoubleSpinBox()
                self.segS[d].setRange(0,100)
                self.segS[d].setSingleStep(1)
                self.segS[d].setValue(s.getS())
                self.segS[d].valueChanged.connect(partial(self.recordSegmentSParameter,d=d))
                rowS[j].addWidget(self.segS[d])
                d = d + 1
            tab3Layout.addRow(rowS[j])

        loadbtn3 = QPushButton("Load from file")
        loadbtn3.clicked.connect(self.openSFileDialog)
        tab3Layout.addRow(loadbtn3)
        
        scroll1 = QScrollArea()
        scroll1.setWidget(tab1)
        scroll1.setWidgetResizable(True)
        scroll1.setFixedHeight(550)
        scroll2 = QScrollArea()
        scroll2.setWidget(tab2)
        scroll2.setWidgetResizable(True)
        scroll2.setFixedHeight(550)
        scroll3 = QScrollArea()
        scroll3.setWidget(tab3)
        scroll3.setWidgetResizable(True)
        scroll3.setFixedHeight(550)
        tabView.addTab(scroll1,"Ease of passing")
        tabView.addTab(scroll2,"Obscurity")
        tabView.addTab(scroll3,"Statistic")
        #buttons = QHBoxLayout()
        #savebutton = QPushButton("Save")
        #closebutton = QPushButton("Close")
        #closebutton.clicked.connect(assignDialog.close)
        #buttons.addWidget(savebutton)
        #buttons.addWidget(closebutton)
        
        assignLayout.addRow(tabView)
        #assignLayout.addRow(buttons)
        assignDialog.setFixedSize(800,600)
        assignDialog.exec_()

    def openBFileDialog(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setNameFilter("CSV (*.csv)")
        #filenames = QStringList()
        #model = QStandardItemModel()	
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            f = open(filenames[0], "r")
			
            with f:
                i_col = 1
                i_row = 1
                d = 0
                for row in csv.reader(f):
                    if i_row<=self.number_h:
                        for field in row:
                            if i_col<=self.number_w:
                                s = self.segments["segments"][d]["obj"]
                                #print("%f" % float(field))
                                s.setC(float(field))
                                self.segC[d].setValue(float(field))
                                d = d+1
                                i_col = i_col+1
                        i_row = i_row+1
                        i_col = 1
                        
                
                    #items = [
                    #    QStandardItem(field)
                    #    for field in row
                    #]
                    #model.appendRow(items)
                    
             

        #ofname = QFileDialog.getOpenFileName(self, 'Open file', '~',"CSV files (*.csv)")
        #f = open(ofname, 'r')
        #with f:
        #    data = f.read()
        #print("%s" % ofname)

    def openOFileDialog(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setNameFilter("CSV (*.csv)")
        #filenames = QStringList()
        #model = QStandardItemModel()	
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            f = open(filenames[0], "r")
			
            with f:
                i_col = 1
                i_row = 1
                d = 0
                for row in csv.reader(f):
                    if i_row<=self.number_h:
                        for field in row:
                            if i_col<=self.number_w:
                                s = self.segments["segments"][d]["obj"]
                                #print("%f" % float(field))
                                s.setO(float(field))
                                self.segO[d].setValue(float(field))
                                d = d+1
                                i_col = i_col+1
                        i_row = i_row+1
                        i_col = 1

    def openSFileDialog(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setNameFilter("CSV (*.csv)")
        #filenames = QStringList()
        #model = QStandardItemModel()	
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            f = open(filenames[0], "r")
			
            with f:
                i_col = 1
                i_row = 1
                d = 0
                for row in csv.reader(f):
                    if i_row<=self.number_h:
                        for field in row:
                            if i_col<=self.number_w:
                                s = self.segments["segments"][d]["obj"]
                                #print("%f" % float(field))
                                s.setS(float(field))
                                self.segS[d].setValue(float(field))
                                d = d+1
                                i_col = i_col+1
                        i_row = i_row+1
                        i_col = 1
                        

    def recordSegmentCParameter(self,value,d=0):
        #print("New C %f at %i" % (value,d))
        s = self.segments["segments"][d]["obj"]
        s.setC(value)

    def recordSegmentOParameter(self,value,d=0):
        #print("New C %f at %i" % (value,d))
        s = self.segments["segments"][d]["obj"]
        s.setO(value)

    def recordSegmentSParameter(self,value,d=0):
        #print("New C %f at %i" % (value,d))
        s = self.segments["segments"][d]["obj"]
        s.setS(value)
        
        
class segmentObj():

    def __init__(self, pos_x, pos_y, c, o, s, h,grid):
        self._posX = pos_x
        self._posY = pos_y
        self._c = c
        self._o = o
        self._s = s
        self._h = h
        self._m = 0
        self._grid = grid
        self._id = "A"+"_"+str(pos_y)+"_"+str(pos_x)

    def getId(self):
        return self._id
    def getPosX(self):
        return self._posX
    def setPosX(self,pos_x):
        self._posX = posX
    
    def getPosY(self):
        return self._posY
    def setPosY(self,pos_y):
        self._posY = posY
        
    def getC(self):
        return self._c
    def setC(self,c):
        self._c = c

    def getO(self):
        return self._o
    def setO(self,o):
        self._o = o
        
    def getS(self):
        return self._s
    def setS(self,s):
        self._s = s

    def getH(self):
        return self._h
    def setH(self,h):
        self._h = h

    def getM(self):
        return self._m
    def setM(self,m):
        self._m = m
                                                           
    def getGrid(self):
        return self._grid
    def setGrid(self, grid):
        self._grid = grid
    

class intruderObj():
    def __init__(self, id, type, arr_time, period):
        self._type = type
        self._id = id
        self._arrTime = arr_time
        self._period = period
        self._isDetected = 0
        self._isInside = 0
        self._currentLoc = None
        self._node = None
        self._path = {"paths": []}

    def getType(self):
        return self._type
    def getId(self):
        return self._id
    def getArrTime(self):
        return self._arrTime
    def isDetected(self):
        return self._isDetected
    def isInside(self):
        return self._isInside
    def moveInside(self):
        self._isInside = 1
    def moveOutside(self):
        self._isInside = 0
    def isDetected(self):
        self._isInside = 0
    def getCurrentLoc(self):
        return self._currentLoc
    def setCurrentLoc(self,loc):
        self._currentLoc = loc
    def getNode(self):
        return self._node
    def setNode(self,node):
        self._node = node
    def getPeriod(self):
        return self._period

    def addPath(self,p,path,graphic):
        self._paths["paths"].append({"p":p,"path":path,"pathgraphic":graphic})
    def getPath(self,p):
        value = [d for d in self._paths["paths"] if d["p"]==p]
        #print(len(value))
        return value[0]["path"]

    def getGPath(self,p):
        value = [d for d in self._paths["paths"] if d["p"]==p]
        #print(len(value))
        return value[0]["pathgraphic"]

    def clearPath(self):
        self._paths = {"paths":[]}

        
class sensorObj():
    def __init__(self, id, startPointX, startPointY, i, j, loc, node):
        self._id = id
        self._startPointX = startPointX
        self._startPointY = startPointY
        self._x = i
        self._y = j
        self._currentloc = loc
        self._startloc = loc
        self._endloc = loc
        self._node = node
        self._paths = {"paths":[]}
        self._collectedM = 0
        self._directionX = 1
        self._directionY = 1
        self._status = 0
        self._busystage = 0

    def getId(self):
        return self._id
    def setStartX(self,startPointX):
        self._startPointX = startPointX
    def getStartX(self):
        return self._startPointX
    def setStartY(self,startPointY):
        self._startPointY = startPointY
    def getStartY(self):
        return self._startPointY
    def setX(self,i):
        self._x = i
    def getX(self):
        return self._x
    def setY(self,j):
        self._y = j
    def getY(self):
        return self._y
    def setDirX(self,directionX):
        self._directionX = directionX
    def getDirX(self):
        return self._directionX
    def setDirY(self,directionY):
        self._directionY = directionY
    def getDirY(self):
        return self._directionY

    def getNode(self):
        return self._node
    def setNode(self,node):
        self._node = node

    def getCurrentLoc(self):
        return self._currentloc

    def setCurrentLoc(self, segment):
        self._currentloc = segment

    def getStartLoc(self):
        return self._startloc
    def setStartLoc(self,segment):
        self._startloc = segment

    def getEndLoc(self):
        return self._endloc
    def setEndLoc(self,segment):
        self._endloc = segment

    def addPath(self,p,path,graphic):
        self._paths["paths"].append({"p":p,"path":path,"pathgraphic":graphic})
    def getPath(self,p):
        value = [d for d in self._paths["paths"] if d["p"]==p]
        #print(len(value))
        return value[0]["path"]

    def getGPath(self,p):
        value = [d for d in self._paths["paths"] if d["p"]==p]
        #print(len(value))
        return value[0]["pathgraphic"]

    def clearPath(self):
        self._paths = {"paths":[]}
    

class Path():
    def __init__(self,start,period,length):
        self._start = start
        self._period = period
        self._length = length
        self._pathsegments = {"segments":[]}
        self._pathM = 0

    def addSegment(self,t,segment):
        self._pathsegments["segments"].append({"t":t,"segment":segment})
    def getSegment(self,t):
        value = [d for d in self._pathsegments["segments"] if d["t"]==t]
        #print(len(value))
        return value[0]["segment"]
    def findSegment(self,segment):
        value = [d for d in self._pathsegments["segments"] if d["segment"]==segment]
        if len(value)>0:
            return value[0]["segment"]
        else:
            return None
    def findSegmentwithT(self,segment,t):
        value = [d for d in self._pathsegments["segments"] if d["segment"]==segment and t-d["t"]<10]
        if len(value)>0:
            return value[0]["segment"]
        else:
            return None
    

#class segmentInPath():
#    def __init__(self,segment,time):
#        self._segment = segment
#        self._time = time
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IDSSim()
    sys.exit(app.exec_())
