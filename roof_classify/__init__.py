"""
/***************************************************************************
 RoofClassify
                                 A QGIS plugin
 this plugin classifies building's roof
                             -------------------
        begin                : 2020-06-22
        copyright            : (C) 2020 by alessandro bacciottini, arjan feta
        email                : arjan.feta@stud.unifi.it
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
    """Load RoofClassify class from file RoofClassify.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .roof_classify import RoofClassify

    return RoofClassify(iface)
