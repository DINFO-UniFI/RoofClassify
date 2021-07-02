"""
/***************************************************************************
 ClassifyRoof
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
import os.path
from pathlib import Path

# Initialize Qt resources from file resources.py
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog

# Import the code for the dialog
from roof_classify.__about__ import DIR_PLUGIN_ROOT, __title__
from roof_classify.gui.roof_classify_dialog import RoofClassifyDialog
from roof_classify.logic import DataClassifier
from roof_classify.toolbelt import PlgLogger


class RoofClassify:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.log = PlgLogger().log
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            self.plugin_dir, "i18n", "RoofClassify_{}.qm".format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

        # Create the dialog (after translation) and keep reference

        self.dlg = RoofClassifyDialog()

        # Declare instance attributes
        self.actions = []

        self.menu = __title__
        self.toolbar = self.iface.addToolBar(__title__)
        self.toolbar.setObjectName(__title__)

        self.dlg.lineEdit.clear()
        self.dlg.pushButton.clicked.connect(self.select_raster)
        self.dlg.lineEdit_2.clear()
        self.dlg.pushButton_2.clicked.connect(self.select_shape)
        self.dlg.lineEdit_3.clear()
        self.dlg.pushButton_3.clicked.connect(self.select_raster_class)
        self.dlg.lineEdit_4.clear()
        self.dlg.pushButton_4.clicked.connect(self.select_output_folder)

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return QCoreApplication.translate(__title__, message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = str(DIR_PLUGIN_ROOT / "resources/images/icon.png")
        self.add_action(
            icon_path,
            text=self.tr("classify roofs"),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(__title__, action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def select_raster(self):  # cartella che contiene i raster da dover classificare
        # filename = QFileDialog.getOpenFileName(self.dlg, "Select raster ","", '*.tif')
        directory = QFileDialog.getExistingDirectory(
            self.dlg, "Seleziona cartella contenente raster da classificare"
        )
        # self.dlg.lineEdit.setText(filename)
        self.dlg.lineEdit.setText(directory)

    def select_shape(self):
        # filename=QFileDialog.getOpenFileName(self.dlg, "select shape","",'*.shp')
        # self.dlg.lineEdit_2.setText(filename)
        directory2 = QFileDialog.getExistingDirectory(
            self.dlg, "Seleziona cartella contenente shape di training"
        )
        self.dlg.lineEdit_2.setText(directory2)

    def select_raster_class(self):
        filename = QFileDialog.getOpenFileName(
            self.dlg, "select training raster", "", "*.tif"
        )
        self.dlg.lineEdit_3.setText(filename)

    def select_output_folder(self):
        out_folder = QFileDialog.getExistingDirectory(
            self.dlg, "Seleziona cartella per output"
        )
        self.dlg.lineEdit_4.setText(out_folder)

    def get_classes_count(self) -> int:
        """Count number of roof types (= classes).

        :return: number of classes (i.e. number of roof types)
        :rtype: int
        """
        roofingShapefileDir = self.dlg.lineEdit_2.text()
        li_shps = Path(roofingShapefileDir).rglob("*.shp")

        return len(list(li_shps))

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            classifier = DataClassifier()

            rasterDirectory = self.dlg.lineEdit.text()
            shapefilesDirectory = self.dlg.lineEdit_2.text()
            trainingRasterFilepath = self.dlg.lineEdit_3.text()
            outputDirectory = self.dlg.lineEdit_4.text()
            self.log(rasterDirectory)
            self.log(shapefilesDirectory)
            self.log(trainingRasterFilepath)

            # Instanciate a random forest classifier
            # Training the classifier
            classifier.train(trainingRasterFilepath, shapefilesDirectory)

            classifiedImages = []
            # Parsing the images to be classified
            for file in Path(rasterDirectory).rglob("*.tif"):
                imgFilepath = str(file)
                self.log(imgFilepath)
                # Classify the image
                classifiedImage = classifier.classifyRoofTypes(imgFilepath)
                # Define an export filepath for the classified image
                outputFilename = (file.name).replace(".tif", "_classsified.tif")
                outputFilepath = outputDirectory / outputFilename
                self.log(outputFilepath)
                # Write the image array into a QgsRasterLayer
                rasterOutput = classifier.writeGeotiff(
                    imgFilepath,
                    classifiedImage,
                    self.get_classes_count(),
                    outputFilepath,
                )
                classifiedImages.append(rasterOutput)

            classifier.mergeRasterLayers(classifiedImages, outputDirectory)
