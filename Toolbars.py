from PyQt5.QtCore import QDir, Qt,QSize,QSettings,QRect,QEvent
from PyQt5.QtGui import QImage, QPainter, QPalette, QPixmap, QPen,QIntValidator,QDoubleValidator
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog,QLabel,QToolBar,QSpacerItem,
        QMainWindow, QMenu,QCheckBox, QMessageBox, QScrollArea, QSizePolicy,QVBoxLayout,QWidget,QFrame,QScrollBar,QHBoxLayout,QTextEdit,QLineEdit,QComboBox)
def CreateToolbars(self):

    Toolbar = QToolBar()
    self.ComboObject=QComboBox()
    self.ComboObject.addItems([" ","Signal","StopSign"])
    Toolbar.setIconSize(QSize(50,50))
    Toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon|Qt.AlignLeading) #<= Toolbuttonstyle
    self.addToolBar(Qt.TopToolBarArea,Toolbar)
    Toolbar.addAction(self.createRoad)
    Toolbar.addAction(self.createjunction)
    Toolbar.addAction(self.createStopLane)
    Toolbar.addSeparator()
    Toolbar.addWidget(self.ComboObject)
    Toolbar.addAction(self.chooseObject)
    Toolbar.addSeparator()
    Toolbar.addAction(self.createNeighbor)
    Toolbar.addAction(self.delNeighbor)
    Toolbar.addAction(self.createOverlap)
    Toolbar.addAction(self.delOverlap)
    Toolbar.addSeparator()
    Toolbar.addAction(self.cancel)
    Toolbar.addAction(self.ruler)


    Toolbar.setMovable(False)
    self.onlyInt = QIntValidator()
    self.onlyFloat=QDoubleValidator()
    self.ToolbarLane = QToolBar()
    self.EditLaneWidth=QLineEdit()
    self.EditLaneWidth.textChanged.connect(self.changeValueWidth)
    self.labelLaneId=QLabel()
    self.EditLaneSpeed=QLineEdit()
    self.EditLaneSpeed.setValidator(self.onlyInt)
    self.EditLaneWidth.setValidator(self.onlyFloat)
    self.ComboLaneBorderLeft = QComboBox(self)
    self.ComboLaneBorderLeft.addItems(["SOLID_WHITE", "DOTTED_WHITE",
                        "CRUB", "SOLID_YELLOW", "DOTTED_YELLOW"])

    self.EditLaneSpeed.setText("15")
    self.EditLaneWidth.setText("3")
    labelLeft=QLabel()
    labelLeft.setText("Left border type (blue)")

    labelRight=QLabel()
    labelRight.setText("Right border type (green)")
    self.ComboLaneBorderRight = QComboBox(self)
    self.ComboLaneBorderRight.addItems(["SOLID_WHITE", "DOTTED_WHITE",
                        "CRUB", "SOLID_YELLOW", "DOTTED_YELLOW"])

    labelWidth=QLabel()
    labelWidth.setText("Width")
    labelSpeed=QLabel()
    labelSpeed.setText("Speed")
    self.ToolbarLane.setIconSize(QSize(300,50))
    self.ToolbarLane.setToolButtonStyle(Qt.ToolButtonTextBesideIcon|Qt.AlignLeft) #<= Toolbuttonstyle
    

   
    self.ToolbarLane.addWidget(self.labelLaneId)
    self.ToolbarLane.addWidget(labelWidth)
    self.ToolbarLane.addWidget(self.EditLaneWidth)
    self.ToolbarLane.addWidget(labelSpeed)
    self.ToolbarLane.addWidget(self.EditLaneSpeed)
    self.useTrajecoryChk = QCheckBox("Use Trajectory for creation")
    self.useTrajecoryChk.setChecked(False)
    self.useTrajecoryChk.stateChanged.connect(self.CreateByTrajectoryChk_changed)
    self.ComboLaneTurn = QComboBox(self)
    self.ComboLaneTurn.addItems(["NO_TURN", "LEFT_TURN",
                        "RIGHT_TURN", "U_TURN"])
    self.ToolbarLane.addWidget( self.ComboLaneTurn)
    self.ToolbarLane.addWidget(self.useTrajecoryChk)
    self.ToolbarLane.addAction(self.acceptRoad)

    self.ToolbarLane.setMovable(True)

    self.ToolbarLaneLeftRight = QToolBar()
    labelInfo=QLabel()
    labelInfo.setText("Start to draw Left border")
    self.ToolbarLaneLeftRight.addWidget(labelLeft)
    self.ToolbarLaneLeftRight.addWidget(self.ComboLaneBorderLeft)
    self.ToolbarLaneLeftRight.addWidget(labelInfo)
    labelInfo=QLabel()
    labelInfo.setText("Start to draw Right border")
    self.ToolbarLaneLeftRight.addWidget(labelRight)
    self.ToolbarLaneLeftRight.addWidget(self.ComboLaneBorderRight)
    self.ToolbarLaneLeftRight.addAction(self.createLeftRight)

   


    self.ComboLaneBorderLeft.currentIndexChanged.connect(self.leftChanged)
    self.ComboLaneBorderRight.currentIndexChanged.connect(self.rightChanged)




    

    self.ToolbarJunction=QToolBar()
    self.ToolbarJunction.addAction(self.getBezier)
    self.ToolbarJunction.addAction(self.acceptjunction)
    self.ToolbarJunction.addAction(self.previewJunction)
    self.ComboJunctionTurn = QComboBox(self)
    self.ComboJunctionTurn.addItems(["NO_TURN", "LEFT_TURN",
                        "RIGHT_TURN", "U_TURN"])

    labelSpeedJk=QLabel()
    labelSpeedJk.setText("Speed")
    self.EditLaneSpeedJk=QLineEdit()
    self.EditLaneSpeedJk.setValidator(self.onlyInt)
    self.ToolbarJunction.addWidget(labelSpeedJk)
    self.ToolbarJunction.addWidget(self.EditLaneSpeedJk)
    self.EditLaneSpeedJk.setText("10")
    self.ToolbarJunction.addWidget( self.ComboJunctionTurn)
    self.changelaneChk = QCheckBox("Lane Change")
    self.changelaneChk.setChecked(False)

    self.ToolbarJunction.addWidget(self.changelaneChk)


    self.ToolbarNeighbor=QToolBar()
    self.NeighborMainLanes = QComboBox(self)

    self.ComboNeighborForwardLeft = QComboBox(self)
    self.ComboNeighborReverseLeft = QComboBox(self)
    self.ComboNeighborForwardRight = QComboBox(self)
    self.ComboNeighborReverseRight = QComboBox(self)


    labelMain=QLabel()
    labelMain.setText("For Lane")


    labelNeighborForwardLeft=QLabel()
    labelNeighborForwardLeft.setText("Left forward neighbor")
    labelNeighborReverseLeft=QLabel()
    labelNeighborReverseLeft.setText("Left reverse neighbor")
    labelNeighborForwardRight=QLabel()
    labelNeighborForwardRight.setText("Right forward neighbor")
    labelNeighborReverseRight=QLabel()
    labelNeighborReverseRight.setText("Right reverse neighbor")


    self.ToolbarNeighbor.addWidget(labelMain)
    self.ToolbarNeighbor.addWidget(self.NeighborMainLanes)
    self.ToolbarNeighbor.addWidget(labelNeighborForwardLeft)
    self.ToolbarNeighbor.addWidget(self.ComboNeighborForwardLeft)
    self.ToolbarNeighbor.addWidget(labelNeighborReverseLeft)  
    self.ToolbarNeighbor.addWidget(self.ComboNeighborReverseLeft)
    self.ToolbarNeighbor.addWidget(labelNeighborForwardRight)  
    self.ToolbarNeighbor.addWidget(self.ComboNeighborForwardRight)
    self.ToolbarNeighbor.addWidget(labelNeighborReverseRight) 
    self.ToolbarNeighbor.addWidget(self.ComboNeighborReverseRight)
    self.ToolbarNeighbor.addAction(self.acceptNeighbor)
    self.ToolbarStopLane=QToolBar()
    self.ToolbarStopLane.addAction(self.acceptStopLane)
    self.ToolbarOverlap=QToolBar()

    self.ComboOverlapLanes = QComboBox(self)
    labelOverlapLane=QLabel()
    labelOverlapLane.setText("Lane object")
    self.ToolbarOverlap.addWidget(labelOverlapLane) 
    self.ToolbarOverlap.addWidget(self.ComboOverlapLanes)

    self.ComboboxesForOverlap=[]
    self.ComboOverlapSignal = QComboBox(self)
    labelOverlapSignal=QLabel()
    labelOverlapSignal.setText("Signal object")
    self.ToolbarOverlap.addWidget(labelOverlapSignal) 
    self.ToolbarOverlap.addWidget(self.ComboOverlapSignal)

    self.ComboOverlapStopSign = QComboBox(self)
    labelOverlapStopSign=QLabel()
    labelOverlapStopSign.setText("Stop sign object")
    self.ToolbarOverlap.addWidget(labelOverlapStopSign) 
    self.ToolbarOverlap.addWidget(self.ComboOverlapStopSign)
    self.ComboboxesForOverlap.append(self.ComboOverlapSignal)
    self.ComboboxesForOverlap.append(self.ComboOverlapStopSign)
    self.ToolbarOverlap.addAction(self.acceptOverlap)
    

    self.ToolbarSignal=QToolBar()

    self.ComboSignalStopLanes=QComboBox(self)
    labelSignalStopLane=QLabel()
    labelSignalStopLane.setText("Choose stoplane")
    self.ToolbarSignal.addWidget(labelSignalStopLane)
    self.ToolbarSignal.addWidget(self.ComboSignalStopLanes)
    self.ToolbarSignal.addAction(self.acceptSignal)


    self.ToolbarStopSign=QToolBar()
    self.ComboLaneForStopSign = QComboBox(self)
    labelStopSign=QLabel()
    labelStopSign.setText("choose stop lane")
    self.ToolbarStopSign.addWidget(labelStopSign) 
    self.ToolbarStopSign.addWidget(self.ComboLaneForStopSign)
    self.ComboLaneForStopSign.currentIndexChanged.connect(self.signToStopLane)
    self.ToolbarStopSign.addAction(self.acceptStopSign)
    
    self.ToolbarDelNeighbor=QToolBar()
    labelIdNeighbor=QLabel()
    labelIdNeighbor.setText("Neighbor id and mainLane")
    self.ComboneighborIdMainLane= QComboBox(self)
    self.labelLeftForward=QLabel()
    self.labelLeftReverse=QLabel()
    self.labelRightForward=QLabel()
    self.labelRightReverse=QLabel()

    self.ComboneighborIdMainLane.currentIndexChanged.connect(self.addLabelForNeighborDeletion)
    self.ToolbarDelNeighbor.addWidget(labelIdNeighbor)
    self.ToolbarDelNeighbor.addWidget(self.ComboneighborIdMainLane)
    self.ToolbarDelNeighbor.addWidget(self.labelLeftForward)
    self.ToolbarDelNeighbor.addWidget(self.labelLeftReverse)
    self.ToolbarDelNeighbor.addWidget(self.labelRightForward)
    self.ToolbarDelNeighbor.addWidget(self.labelRightReverse)
    self.ToolbarDelNeighbor.addAction(self.finishNeighborDeletion)

    self.ToolbarDelOverlap=QToolBar()

    labelDelOverlap=QLabel()
    labelDelOverlap.setText("Choose overlap")

    self.ComboDelOverlap=QComboBox(self)
    
    self.ToolbarDelOverlap.addWidget(labelDelOverlap)
    self.ToolbarDelOverlap.addWidget(self.ComboDelOverlap)

    self.ToolbarDelOverlap.addAction(self.finishOverlapDeletion)
   
    