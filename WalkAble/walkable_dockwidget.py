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

from urllib import urlopen, quote_plus
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
        
        self.tool_pick = PickPointTool(self.canvas)
        self.tool_pick.canvasClicked.connect(self.pointPicked)
        self.prev_tool = QgsMapCanvas.mapTool(self.canvas)
        self.pick_target = ''
        
        self.feedback_id = ''
        self.from_pt = QgsPoint()
        self.to_pt = QgsPoint()
        
        self.feedback_marker = QgsVertexMarker(self.canvas)
        self.from_marker = QgsVertexMarker(self.canvas)
        self.to_marker = QgsVertexMarker(self.canvas)

        #add logo
        self.label_6 = QtGui.QLabel(self.dockWidgetContents)
        self.label_6.setPixmap(QtGui.QPixmap(":/plugins/WalkAble/UI_Logo.png"))
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 0, 0, 1, 1)

        
        #  my profile tab
        self.button_skip.clicked.connect(self.skipLogin)

        # view map tab
        self.slider_directness.sliderReleased.connect(self.updateMap)
        self.slider_comfort.sliderReleased.connect(self.updateMap)
        self.slider_utility.sliderReleased.connect(self.updateMap)
        self.slider_directness.valueChanged.connect(lambda:self.label_weight_directness.setText(str(self.slider_directness.value())))
        self.slider_comfort.valueChanged.connect(lambda:self.label_weight_comfort.setText(str(self.slider_comfort.value())))
        self.slider_utility.valueChanged.connect(lambda:self.label_weight_utility.setText(str(self.slider_utility.value())))
        self.button_reset_map.clicked.connect(self.resetMap)

        # navigate tab
        self.button_from_address.clicked.connect(self.fromAddress)
        self.button_from_pick.clicked.connect(self.fromPick)
        self.button_from_position.clicked.connect(self.fromPosition)
        self.button_to_address.clicked.connect(self.toAddress)
        self.button_to_pick.clicked.connect(self.toPick)
        self.button_find_route.clicked.connect(self.findRoute)
        self.button_reset_route.clicked.connect(self.resetRoute)
        
        # comment tab
        self.button_frommap.clicked.connect(self.pickFromMap)
        self.button_position.clicked.connect(self.getCurrentPosition)
        self.button_submit.clicked.connect(self.submitFeedback)
        self.button_clear.clicked.connect(self.clearFeedback)
        
        self.slider_rating_comfort.valueChanged.connect(lambda:self.label_rating_comfort.setText(str(self.slider_rating_comfort.value())))
        self.slider_rating_utility.valueChanged.connect(lambda:self.label_rating_utility.setText(str(self.slider_rating_utility.value())))
        
        # disable tabs at startup
        
        for i in [1,2,3]:
            self.tab_container.setTabEnabled(i, False)
        
        # clear scene and load data
        
        clearScene(self.canvas)
        
        self.iface.addProject(os.path.dirname(__file__) + os.path.sep + 'walkable_sample_data' + os.path.sep + 'walkable_sample_data.qgs')
        
        self.street_layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if "Streets.shp" in lyr.source():
                self.street_layer = lyr
                break
        
        self.canvas.setExtent(self.street_layer.extent().buffer(100))
        self.canvas.refresh()

    def closeEvent(self, event):
        clearScene(self.canvas)
        self.closingPlugin.emit()
        event.accept()

    #--------------------------------------------------------------------------
    
    # my profile tab
    
    def skipLogin(self):
        
        self.tab_container.setCurrentWidget(self.tab_view)
        for i in [1,2,3]:
            self.tab_container.setTabEnabled(i, True)
    
    # view map tab
    
    def updateMap(self):
    
        layer = self.street_layer
    
        wgt_d = self.slider_directness.value()
        wgt_c = self.slider_comfort.value()
        wgt_u = self.slider_utility.value()
        
        if wgt_d + wgt_c + wgt_u == 0:
            self.slider_directness.setValue(1)
            self.updateMap()
            
        else:
            
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
 
    def resetMap(self):
        
        self.slider_directness.setValue(5)
        self.slider_comfort.setValue(5)
        self.slider_utility.setValue(5)
        
        self.canvas.setExtent(self.street_layer.extent().buffer(100))
        self.updateMap()
        
    # navigate tab
    
    def fromPick(self):
        self.pick_target = 'from'
        self.prev_tool = QgsMapCanvas.mapTool(self.canvas)
        self.canvas.setMapTool(self.tool_pick)
    
    def fromAddress(self):
        print str(self.line_route_from.text)
        self.pick_target = 'from'
        self.pointPicked(getCoords(str(self.line_route_from.text()), self.street_layer))
    
    def fromPosition(self):
        self.pick_target = 'from'
        self.pointPicked(QgsPoint(91919, 437600)) 
    
    def toPick(self):
        self.pick_target = 'to'
        self.prev_tool = QgsMapCanvas.mapTool(self.canvas)
        self.canvas.setMapTool(self.tool_pick)
    
    def toAddress(self, point):
        self.pick_target = 'to'
        self.pointPicked(getCoords(str(self.line_route_to.text()), self.street_layer))    
    
    def findRoute(self):
    
        clearRoutes(self.canvas)
        
        network_layer = self.street_layer
        
        # get the points to be used as origin and destination
        from_to_pts = [self.from_pt, self.to_pt]
        print from_to_pts
        
        # build the graph including these points
        director = QgsLineVectorLayerDirector(network_layer, -1, '', '', '', 3)
        properter = WeightedDistanceProperter() # length/rating as cost
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

                for p in points:
                    rb.addPoint(p)
                
                self.canvas.setExtent(rb.asGeometry().boundingBox().buffer(100))
                self.canvas.refresh()
        
    def resetRoute(self):
        
        clearMarker(self.canvas, self.from_marker)
        clearMarker(self.canvas, self.to_marker)
        clearRoutes(self.canvas)
        
        self.line_route_from.clear()
        self.line_route_to.clear()
    
    
    # comment tab
    
    def getCurrentPosition(self):
    
        self.pick_target = 'comment'
        self.pointPicked(QgsPoint(91919, 437600)) 
    
    def pickFromMap(self):
        
        self.pick_target = 'comment'
        self.prev_tool = QgsMapCanvas.mapTool(self.canvas)
        self.canvas.setMapTool(self.tool_pick)
    
    def submitFeedback(self):
    
        db_file = 'feedback.csv'
        
        user_id = '987654321'
        
        street_id = self.feedback_id
        
        feedback_comfort, feedback_utility = '', ''
        if self.check_comfort.isChecked():
            feedback_comfort += str(self.slider_rating_comfort.value())
        if self.check_utility.isChecked():
            feedback_utility += str(self.slider_rating_utility.value())
        
        feedback_comment = str(self.field_comment.toPlainText())
        
        with open(os.path.dirname(__file__) + os.path.sep + db_file, 'a') as f:
            f.write(';'.join([user_id, street_id, feedback_comfort, feedback_utility, feedback_comment])+'\n')
        
        self.iface.messageBar().pushMessage("Success", "Feedback submitted, thank you!", level=QgsMessageBar.INFO, duration=5)
        
        self.clearFeedback()
    
    def clearFeedback(self):
        
        clearMarker(self.canvas, self.feedback_marker)
        
        self.feedback_street = None
        self.line_street.clear()
        
        self.check_comfort.setChecked(False)
        self.check_utility.setChecked(False)
        
        self.slider_rating_comfort.setValue(3)
        self.slider_rating_utility.setValue(3)
        
        self.field_comment.clear()
    
    
    def pointPicked(self, cpoint):
    
        if cpoint:
            point = QgsPoint(cpoint.x(), cpoint.y())
            street = getNearest(self.street_layer, point)
            
            if self.pick_target == 'comment':
                field = self.line_street
                addMarker(self.canvas, self.feedback_marker, point, QtGui.QColor(255,0,0))
                self.feedback_id = str(street['wvk_id'])
            elif self.pick_target == 'from':
                field = self.line_route_from
                addMarker(self.canvas, self.from_marker, point, QtGui.QColor(0,0,255))
                self.from_pt = point
            elif self.pick_target == 'to':
                field = self.line_route_to
                addMarker(self.canvas, self.to_marker, point, QtGui.QColor(0,255,0))
                self.to_pt = point
            
            field.setText(street['stt_naam'])
        
        self.canvas.setMapTool(self.prev_tool)

#--------------------------------------------------------------------------

def addMarker(canvas, marker, point, color):
    
    canvas.scene().addItem(marker)
    marker.setCenter(point)
    marker.setColor(color)
    marker.setIconSize(10)
    marker.setIconType(QgsVertexMarker.ICON_BOX)
    marker.setPenWidth(3)

def clearMarker(canvas, marker):
    
    if marker in canvas.scene().items():
        canvas.scene().removeItem(marker)
    
def clearRoutes(canvas):

    rb_items = [i for i in canvas.scene().items() if issubclass(type(i), QgsRubberBand)]
    for rb in rb_items:
        if rb in canvas.scene().items():
            canvas.scene().removeItem(rb)

def clearScene(canvas):
    
        for rb in [i for i in canvas.scene().items() if issubclass(type(i), QgsRubberBand)]:
            if rb in canvas.scene().items():
                canvas.scene().removeItem(rb)
        for vm in [i for i in canvas.scene().items() if issubclass(type(i), QgsVertexMarker)]:
            if vm in canvas.scene().items():
                canvas.scene().removeItem(vm)
            
def getNearest(layer, point):
    
    spi = QgsSpatialIndex(layer.getFeatures())
    
    nearest_id = spi.nearestNeighbor(point, 1)[0]
    
    # https://gis.stackexchange.com/a/118651
    nnfeature = layer.getFeatures(QgsFeatureRequest(nearest_id)).next()
    # Get the distance to this feature (it is not necessarily the nearest one)
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

def getCoords(address, layer):
        
    url = "http://nominatim.openstreetmap.org/search?format=jsonv2&q="
    try:
        req = urlopen(url + quote_plus(address))
        lst = json.loads(req.read().decode('utf-8'))
        loc = QgsPoint(float(lst[0]['lon']), float(lst[0]['lat']))
    except:
        # when something goes wrong, e.g. timeout
        return None
    
    # transform WGS84 coords to local CRS
    point = QgsCoordinateTransform(QgsCoordinateReferenceSystem(4326), layer.crs()).transform(loc)
    
    return point
    
# based on code provided by @jorgegil
class WeightedDistanceProperter(QgsArcProperter):
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


# based on code from https://stackoverflow.com/a/19985550
class PickPointTool(QgsMapToolEmitPoint):
    
    def canvasPressEvent(self, event):
        pass
    
    def canvasReleaseEvent(self, event):
        self.canvasClicked.emit(event.mapPoint(), event.button())
        super(PickPointTool, self).canvasReleaseEvent(event)

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