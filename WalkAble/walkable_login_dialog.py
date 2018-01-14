import os

from PyQt4 import QtGui, QtCore, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'walkable_login_dialog.ui'))

class WalkAbleLoginDialog(QtGui.QDialog, FORM_CLASS):

    closingPlugin = QtCore.pyqtSignal()

    def __init__(self, iface, dockwidget):
        
        super(WalkAbleLoginDialog, self).__init__(None)
        self.setupUi(self)
        
        self.iface = iface
        self.dockwidget = dockwidget
        
        self.button_login.clicked.connect(self.openDockwidget)
    
    
    def openDockwidget(self):
        self.iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dockwidget)
        self.dockwidget.show()
        self.close()