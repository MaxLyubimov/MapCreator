from PyQt5.QtCore import QDir, Qt,QSize,QSettings,QRect,QEvent
from PyQt5.QtGui import QImage, QPainter, QPalette, QPixmap, QPen
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,QToolBar,
        QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy,QVBoxLayout,QWidget,QFrame,QScrollBar,QHBoxLayout)
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
class Pane(QScrollArea):

    def __init__(self, alignment=0, parent=None):
        super().__init__(parent)
        self.mainWidget = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mainWidget)
        self.mainLayout.setAlignment(alignment)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameStyle(QFrame.NoFrame)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Ignored,
                           QSizePolicy.Ignored)
        self.setWidgetResizable(True)
        self.setWidget(self.mainWidget)
        
    def wheelEvent(self, ev):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            return False
        super(Pane, self).wheelEvent(ev)
    def addWidget(self, widget):
        self.mainLayout.addWidget(widget)

    def removeWidget(self, widget):
        self.mainLayout.removeWidget(widget)