"""
/***************************************************************************
 RoofClassifyDialog
                                 A QGIS plugin
 this plugin classifies building's roof
                             -------------------
        begin                : 2020-06-22
        git sha              : $Format:%H$
        copyright            : (C) 2020 by alessandro bacciottini, arjan feta
        email                : arjan.feta@stud.unifi.it
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

# standard
from pathlib import Path

# PyQGIS
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog

# plugin
from roof_classify.__about__ import __title__, __version__

# -- Globals
FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "{}_base.ui".format(Path(__file__).stem)
)


# -- Classes


class RoofClassifyDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(RoofClassifyDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(f"{__title__} - v{__version__}")
