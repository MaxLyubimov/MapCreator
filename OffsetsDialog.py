from PyQt5.QtCore import QDir, Qt,QSize,QSettings,QRect,QEvent,QFile
from PyQt5.QtGui import QImage, QPainter, QPalette, QPixmap, QPen,QIcon,QDoubleValidator
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,QToolBar,QDialog,QLineEdit,
        QSizePolicy,QVBoxLayout,QWidget,QFrame,QScrollBar,QHBoxLayout,QTextEdit,QDialogButtonBox)


class OffsetsDialog(QDialog):
    def __init__(self, offsetX,offsetY,rotation):
        super(OffsetsDialog, self).__init__(None)

        layout = QVBoxLayout(self)
        offsetX=str(offsetX).replace(".",",")
        offsetY=str(offsetY).replace(".",",")
        rotation=str(rotation).replace(".",",")
        # nice widget for editing the date
        labelX=QLabel()
        labelX.setText("Offset X")
        self.offsetX = QLineEdit(self)
        self.offsetX.setText(str(offsetX))
        labelY=QLabel()
        labelY.setText("Offset Y")
        self.offsetY = QLineEdit(self)
        self.offsetY.setText(str(offsetY))
        labelR=QLabel()
        labelR.setText("Rotation")
        self.rotation = QLineEdit(self)
        self.rotation.setText(str(rotation))
        
        self.onlyFloat=QDoubleValidator()
        self.offsetX.setValidator(self.onlyFloat)
        self.offsetY.setValidator(self.onlyFloat)
        self.rotation.setValidator(self.onlyFloat)
        # OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(labelX)
        layout.addWidget(self.offsetX)
        layout.addWidget(labelY)
        layout.addWidget(self.offsetY)
        layout.addWidget(labelR)
        layout.addWidget(self.rotation)
        layout.addWidget(buttons)
        

    # get current date and time from the dialog
    def getOffsetsFromEdit(self):
        return self.offsetX.text(),self.offsetY.text(),self.rotation.text()

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getOffsets(offsetX,offsetY,rotation):
        dialog = OffsetsDialog(offsetX,offsetY,rotation)
        result = dialog.exec_()
        x,y,rotation = dialog.getOffsetsFromEdit()
        x=float(x.replace(",","."))
        y=float(y.replace(",","."))
        rotation=float(rotation.replace(",","."))

        return (x,y,rotation, result == QDialog.Accepted)