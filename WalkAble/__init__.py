# -*- coding: utf-8 -*-
"""
/***************************************************************************
 WalkAble
                                 A QGIS plugin
 Measures walkability in an urban area
                             -------------------
        begin                : 2017-12-13
        copyright            : (C) 2017 by Salko, Anastasiadou, Tsakalakidou
        email                : heikki.salko@aalto.fi
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load WalkAble class from file WalkAble.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .walkable import WalkAble
    return WalkAble(iface)
