# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FreehandRasterGeoreferencer
                                 A QGIS plugin
 Interactive georeferencing of rasters
                             -------------------
        begin                : 2014-05-21
        copyright            : (C) 2014 by GV
        email                : guilhem.vellut@gmail.com
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

def classFactory(iface):
    # load FreehandRasterGeoreferencer class from file FreehandRasterGeoreferencer
    from freehandrastergeoreferencer import FreehandRasterGeoreferencer
    return FreehandRasterGeoreferencer(iface)
