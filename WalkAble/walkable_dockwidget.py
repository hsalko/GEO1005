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
        
        #load data
        self.iface.addProject(os.path.dirname(__file__) + os.path.sep + 'walkable_sample_data.qgs')

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    #--------------------------------------------------------------------------
    
    def getCurrentPosition(self):
    
        print 
    
    def pickFromMap(self):
        
        prev_tool = QgsMapCanvas.mapTool(self.canvas)
        tool = PointTool(self, prev_tool)
        self.canvas.setMapTool(tool)
    
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
        
        with open(os.path.dirname(__file__) + os.path.sep + db_file, 'a') as f:
            f.write(';'.join([user_id, street_id, feedback_comfort, feedback_utility, feedback_comment]))
            f.write('\n')
        
        self.iface.messageBar().pushMessage("Success", "Feedback submitted, thank you!", level=QgsMessageBar.INFO, duration=5)
        
        self.clearFeedback()
    
    def clearFeedback(self):
    
        self.check_comfort.setChecked(False)
        self.check_utility.setChecked(False)
        
        self.slider_rating_comfort.setValue(5)
        self.slider_rating_utility.setValue(5)
        
        self.field_comment.clear()
        
# based on code form: https://gis.stackexchange.com/questions/45094/how-to-programatically-check-for-a-mouse-click-in-qgis
class PointTool(QgsMapTool):   
    def __init__(self, caller, prev_tool):
        self.caller = caller
        self.canvas = caller.canvas
        self.prev_tool = prev_tool
        QgsMapTool.__init__(self, self.canvas)

    def canvasPressEvent(self, event):
        pass

    def canvasMoveEvent(self, event):
        pass

    def canvasReleaseEvent(self, event):
        
        point = event.mapPoint()
        
        self.caller.iface.messageBar().pushMessage("Clicked", str(point), level=QgsMessageBar.INFO, duration=3)
        
        vertex_items = [i for i in self.canvas.scene().items() if issubclass(type(i), QgsVertexMarker)]
        for ver in vertex_items:
            if ver in self.canvas.scene().items():
                self.canvas.scene().removeItem(ver)
        
        marker = QgsVertexMarker(self.canvas)
        marker.setCenter(point)
        marker.setColor(QtGui.QColor(255,0,0))
        marker.setIconSize(10)
        marker.setIconType(QgsVertexMarker.ICON_BOX)
        marker.setPenWidth(3)
        
        self.deactivate()

    def activate(self):
        pass

    def deactivate(self):
        self.canvas.setMapTool(self.prev_tool)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return True

    def isEditTool(self):
        return False