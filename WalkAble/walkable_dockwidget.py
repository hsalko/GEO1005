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

from urllib2 import urlopen
from urllib import quote_plus
import json

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
        
        self.tool_pick = QgsMapToolEmitPoint(self.canvas)
        self.tool_pick.canvasClicked.connect(self.pointPicked)
        self.prev_tool = QgsMapCanvas.mapTool(self.canvas)
        
        self.feedback_street = None

        # login button
        #self.button_login.clicked.connect(self.)

        # change map tab
        self.button_update.clicked.connect(self.updateMap)
        self.button_route_find.clicked.connect(self.findRoute)
        #self.button_route_from.clicked.connect(self.)
        #self.button_route_to.clicked.connect(self.)

        # leave feedback tab
        self.button_frommap.clicked.connect(self.pickFromMap)
        self.button_position.clicked.connect(self.getCurrentPosition)
        self.button_submit.clicked.connect(self.submitFeedback)
        self.button_clear.clicked.connect(self.clearFeedback)
        
        
        
        # sliders
        self.slider_directness.valueChanged.connect(lambda:self.label_weight_directness.setText(str(self.slider_directness.value())))
        self.slider_comfort.valueChanged.connect(lambda:self.label_weight_comfort.setText(str(self.slider_comfort.value())))
        self.slider_utility.valueChanged.connect(lambda:self.label_weight_utility.setText(str(self.slider_utility.value())))
        self.slider_rating_comfort.valueChanged.connect(lambda:self.label_rating_comfort.setText(str(self.slider_rating_comfort.value())))
        self.slider_rating_utility.valueChanged.connect(lambda:self.label_rating_utility.setText(str(self.slider_rating_utility.value())))
        
        #load data
        self.iface.addProject(os.path.dirname(__file__) + os.path.sep + 'walkable_sample_data' + os.path.sep + 'walkable_sample_data.qgs')
        
        self.street_layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if "Streets.shp" in lyr.source():
                self.street_layer = lyr
                break
        
        self.updateMap()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

#--------------------------------------------------------------------------
    
    def updateMap(self):
    
        layer = self.street_layer
    
        wgt_d = self.slider_directness.value()
        wgt_c = self.slider_comfort.value()
        wgt_u = self.slider_utility.value()
        
        scaling = 15. / (wgt_d + wgt_c + wgt_u)
        
        idx_d = layer.fieldNameIndex('directness')
        idx_c = layer.fieldNameIndex('comfort')
        idx_u = layer.fieldNameIndex('utility')
        idx_w = layer.fieldNameIndex('weighted')
        
        layer.startEditing()
        for segment in layer.getFeatures():
            attrs = segment.attributes()
            try:
                weitd = scaling * (attrs[idx_d] * wgt_d + attrs[idx_c] * wgt_c + attrs[idx_u] * wgt_u)
                layer.changeAttributeValue(segment.id(), idx_w, weitd)
            except:
                pass
        layer.commitChanges()
 

 
    
    def findRoute(self):
    
        network_layer = self.street_layer
        
        # get the points to be used as origin and destination
        from_to_pts = [QgsPoint(x,y) for (x,y) in [(91919, 437600), (94680, 435270)]]
        
        # build the graph including these points
        director = QgsLineVectorLayerDirector(network_layer, -1, '', '', '', 3)
        properter = WeightedLengthProperter() # length/rating as cost
        director.addProperter(properter)
        builder = QgsGraphBuilder(network_layer.crs())
        tied_points = director.makeGraph(builder, from_to_pts)
        graph = builder.graph()
    
        # calculate the shortest path for the given origin and destination
        
        points = []
        
        if graph:
            
            from_point = tied_points[0]
            to_point = tied_points[1]
            
            from_id = graph.findVertex(from_point)
            to_id = graph.findVertex(to_point)

            (tree, cost) = QgsGraphAnalyzer.dijkstra(graph, from_id, 0)

            if tree[to_id] == -1:
                pass
            else:
                curPos = to_id
                while curPos != from_id:
                    points.append(graph.vertex(graph.arc(tree[curPos]).inVertex()).point())
                    curPos = graph.arc(tree[curPos]).outVertex()
                points.append(from_point)
                points.reverse()
            
                rb = QgsRubberBand(self.canvas)
                rb.setColor(QtGui.QColor(255,0,0))
                rb.setWidth(3)

                for pnt in points:
                    rb.addPoint(pnt)
        
    
    
    def getCurrentPosition(self):
    
        self.pointPicked(QgsPoint(91919, 437600)) 
    
    def pickFromMap(self):
        
        self.prev_tool = QgsMapCanvas.mapTool(self.canvas)
        self.canvas.setMapTool(self.tool_pick)
    
    def pointPicked(self, point):
    
        self.feedback_street = getNearest(self.street_layer, point)
        
        self.line_street.setText(self.feedback_street['stt_naam'])
        
        clearMarkers(self.canvas)
        
        marker = QgsVertexMarker(self.canvas)
        marker.setCenter(point)
        marker.setColor(QtGui.QColor(255,0,0))
        marker.setIconSize(10)
        marker.setIconType(QgsVertexMarker.ICON_BOX)
        marker.setPenWidth(3)
        
        self.canvas.setMapTool(self.prev_tool)
    
    def submitFeedback(self):
    
        db_file = 'feedback.csv'
        
        user_id = '987654321'
        
        street_id = str(self.feedback_street['wvk_id'])[:9]
        
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
        
        clearMarkers(self.canvas)
        
        self.feedback_street = None
        self.line_street.clear()
        
        self.check_comfort.setChecked(False)
        self.check_utility.setChecked(False)
        
        self.slider_rating_comfort.setValue(3)
        self.slider_rating_utility.setValue(3)
        
        self.field_comment.clear()

#--------------------------------------------------------------------------

def clearMarkers(canvas):
        
        vertex_items = [i for i in canvas.scene().items() if issubclass(type(i), (QgsVertexMarker, QgsRubberBand))]
        for ver in vertex_items:
            if ver in canvas.scene().items():
                canvas.scene().removeItem(ver)
        
def getNearest(layer, point):
    
    spi = QgsSpatialIndex(layer.getFeatures())
    
    nearest_id = spi.nearestNeighbor(point, 1)[0]
    
    # https://gis.stackexchange.com/a/118651
    nnfeature = layer.getFeatures(QgsFeatureRequest(nearest_id)).next()
    # Get the distance to this feature (it is not necessarily the nearest one)
    print nnfeature.geometry().closestVertex(point)
    mindistance = point.distance(nnfeature.geometry().closestVertex(point)[0])
    px = point.x()
    py = point.y()
    # Get all the features that may be closer to the point than nnfeature and compare
    closefeatureids = spi.intersects(QgsRectangle(px - mindistance, py - mindistance, px + mindistance, py + mindistance))
    for closefeatureid in closefeatureids:
        closefeature = layer.getFeatures(QgsFeatureRequest(closefeatureid)).next()
        thisdistance = point.distance(closefeature.geometry().closestVertex(point)[0])
        if thisdistance < mindistance:
            mindistance = thisdistance
            nnfeature = closefeature
            if mindistance == 0:
                 break
    
    return nnfeature

def getCoords(address):
        
    url = "http://nominatim.openstreetmap.org/search?format=jsonv2&q="
    try:
        req = urlopen(url + quote_plus(address))
        lst = json.loads(req.read().decode('utf-8'))
        loc = map(float, [lst[0]['lat'], lst[0]['lon']])
    except:
        # when something goes wrong, e.g. timeout: return empty tuple
        return ()
    # otherwise, return the found WGS'84 coordinate
    return tuple(loc)

class WeightedLengthProperter(QgsArcProperter):
    def __init__(self):
        QgsArcProperter.__init__(self)
        self.weighted_index = 9

    def property(self, distance, feature):
        try:
            cost = distance / float(feature.attributes()[self.weighted_index])
            return cost
        except:
            return distance

    def requiredAttributes(self):
        return [self.weighted_index]

"""        
        # store the route results in temporary layer called "Routes"
        routes_layer = uf.getLegendLayerByName(self.iface, "Routes")
        # create one if it doesn't exist
        if not routes_layer:
            attribs = ['id']
            types = [QtCore.QVariant.String]
            routes_layer = uf.createTempLayer('Routes','LINESTRING',self.network_layer.crs().postgisSrid(), attribs, types)
            uf.loadTempLayer(routes_layer)
        
        # insert route line
        for route in routes_layer.getFeatures():
            print route.id()
        uf.insertTempFeatures(routes_layer, [points], [['testing',100.00]])
        buffer = processing.runandload('qgis:fixeddistancebuffer',routes_layer,10.0,5,False,None)
        #self.refreshCanvas(routes_layer)

    def deleteRoutes(self):
        routes_layer = uf.getLegendLayerByName(self.iface, "Routes")
        if routes_layer:
            ids = uf.getAllFeatureIds(routes_layer)
            routes_layer.startEditing()
            for id in ids:
                routes_layer.deleteFeature(id)
            routes_layer.commitChanges()
    
    
"""         
"""       
    def getAddress(point):
        
        url = "http://nominatim.openstreetmap.org/reverse?format=jsonv2&"
        query = 'lat={}&lon={}'.format(lat, lon) # ___FIX_THIS___
        try:
            req = urlopen(url + query)
            lst = json.loads(req.read().decode('utf-8'))
            stn = lst['address']['road']
            
        except:
            # when something goes wrong, e.g. timeout: return empty tuple
            return ()
        # otherwise, return the found WGS'84 coordinate
        return tuple(loc)
     
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
        self.deactivate()

    def activate(self):
        pass

    def deactivate(self):
        ### emit point
        self.canvas.setMapTool(self.prev_tool)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return True

    def isEditTool(self):
        return False
"""