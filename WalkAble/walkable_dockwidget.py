# -*- coding: utf-8 -*-
"""
/***************************************************************************
 WalkAbleDockWidget
                                 A QGIS plugin
 Measures walkability in an urban area
                             -------------------
        begin                : 2017-12-13
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Salko, Anastasiadou, Tsakalakidou
        email                : heikki.salko@aalto.fi
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, QtCore, uic

from qgis.core import *
from qgis.gui import *
from qgis.networkanalysis import *

import processing

# Initialize Qt resources from file resources.py
import resources


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'walkable_dockwidget_base.ui'))


class WalkAbleDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = QtCore.pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(WalkAbleDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        # define globals
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        #self.iface.projectRead.connect(self.updateLayers)
        #self.iface.newProjectCreated.connect(self.updateLayers)
        #self.iface.legendInterface().itemRemoved.connect(self.updateLayers)
        #self.iface.legendInterface().itemAdded.connect(self.updateLayers)

        # login button
        #self.button_login.clicked.connect(self.)

        # change map tab
        #self.button_update.clicked.connect(self.)
        #self.button_route_find.clicked.connect(self.)
        #self.button_route_from.clicked.connect(self.)
        #self.button_route_to.clicked.connect(self.)

        # leave feedback tab
        self.button_frommap.clicked.connect(self.pickFromMap)
        self.button_position.clicked.connect(self.getCurrentPosition)
        self.button_submit.clicked.connect(self.submitFeedback)
        self.button_clear.clicked.connect(self.clearFeedback)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    #--------------------------------------------------------------------------
    
    def getCurrentPosition(self):
    
        pass
    
    def pickFromMap(self):
        
        pass
    
    def submitFeedback(self):
    
        db_file = 'feedback.csv'
        
        user_id = '987654321'
        street_id = '123456789'
        
        feedback_comfort, feedback_utility = '', ''
        if self.check_comfort.isChecked():
            feedback_comfort += str(self.slider_rating_comfort.value())
        if self.check_utility.isChecked():
            feedback_utility += str(self.slider_rating_utility.value())
        
        feedback_comment = str(self.field_comment.toPlainText())
        
        #with open(db_file, 'a') as f:
        #    f.write(';'.join([user_id, street_id, feedback_comfort, feedback_utility, feedback_comment]))
        #    f.write('\n')
        print ';'.join([user_id, street_id, feedback_comfort, feedback_utility, feedback_comment])
    
    def clearFeedback(self):
    
        self.check_comfort.setChecked(False)
        self.check_utility.setChecked(False)
        
        self.slider_rating_comfort.setValue(5)
        self.slider_rating_utility.setValue(5)
        
        self.field_comment.clear()