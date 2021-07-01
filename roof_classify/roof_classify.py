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
import glob
import os
import os.path
from pathlib import Path

# 3rd party
import numpy as np

# Initialize Qt resources from file resources.py
from osgeo import gdal
from qgis import processing
from qgis.core import QgsRasterLayer, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
except Exception:
    import site

    from roof_classify.__about__ import DIR_PLUGIN_ROOT

    site.addsitedir(DIR_PLUGIN_ROOT / "embedded_external_libs")
    from roof_classify.embedded_external_libs.sklearn.ensemble import (
        RandomForestClassifier,
    )
    from roof_classify.embedded_external_libs.sklearn.svm import SVC

# Import the code for the dialog
from roof_classify.__about__ import DIR_PLUGIN_ROOT, __title__
from roof_classify.gui.roof_classify_dialog import RoofClassifyDialog
from roof_classify.toolbelt import PlgLogger

# creo un set di colori pseudocasuali da usare poi nella classificazione
COLORS = [
    "#000000",
    "#FFFF00",
    "#1CE6FF",
    "#FF34FF",
    "#FF4A46",
    "#008941",
    "#006FA6",
    "#A30059",
    "#FFDBE5",
    "#7A4900",
    "#0000A6",
    "#63FFAC",
    "#B79762",
    "#004D43",
    "#8FB0FF",
    "#997D87",
    "#5A0007",
    "#809693",
    "#FEFFE6",
    "#1B4400",
    "#4FC601",
    "#3B5DFF",
    "#4A3B53",
    "#FF2F80",
    "#61615A",
    "#BA0900",
    "#6B7900",
    "#00C2A0",
    "#FFAA92",
    "#FF90C9",
    "#B903AA",
    "#D16100",
    "#DDEFFF",
    "#000035",
    "#7B4F4B",
    "#A1C299",
    "#300018",
    "#0AA6D8",
    "#013349",
    "#00846F",
    "#372101",
    "#FFB500",
    "#C2FFED",
    "#A079BF",
    "#CC0744",
    "#C0B9B2",
    "#C2FF99",
    "#001E09",
    "#00489C",
    "#6F0062",
    "#0CBD66",
    "#EEC3FF",
    "#456D75",
    "#B77B68",
    "#7A87A1",
    "#788D66",
    "#885578",
    "#FAD09F",
    "#FF8A9A",
    "#D157A0",
    "#BEC459",
    "#456648",
    "#0086ED",
    "#886F4C",
    "#34362D",
    "#B4A8BD",
    "#00A6AA",
    "#452C2C",
    "#636375",
    "#A3C8C9",
    "#FF913F",
    "#938A81",
    "#575329",
    "#00FECF",
    "#B05B6F",
    "#8CD0FF",
    "#3B9700",
    "#04F757",
    "#C8A1A1",
    "#1E6E00",
    "#7900D7",
    "#A77500",
    "#6367A9",
    "#A05837",
    "#6B002C",
    "#772600",
    "#D790FF",
    "#9B9700",
    "#549E79",
    "#FFF69F",
    "#201625",
    "#72418F",
    "#BC23FF",
    "#99ADC0",
    "#3A2465",
    "#922329",
    "#5B4534",
    "#FDE8DC",
    "#404E55",
    "#0089A3",
    "#CB7E98",
    "#A4E804",
    "#324E72",
    "#6A3A4C",
    "#83AB58",
    "#001C1E",
    "#D1F7CE",
    "#004B28",
    "#C8D0F6",
    "#A3A489",
    "#806C66",
    "#222800",
    "#BF5650",
    "#E83000",
    "#66796D",
    "#DA007C",
    "#FF1A59",
    "#8ADBB4",
    "#1E0200",
    "#5B4E51",
    "#C895C5",
    "#320033",
    "#FF6832",
    "#66E1D3",
    "#CFCDAC",
    "#D0AC94",
    "#7ED379",
    "#012C58",
]


"""
For more information on the implementation of random forests and SVM classifiers,
see documentation below:
* http://scikit-learn.org/dev/modules/generated/sklearn.ensemble.RandomForestClassifier.html
* http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html
"""
CLASSIFIERS = {
    "random-forest": RandomForestClassifier(
        n_jobs=4, n_estimators=10, class_weight="balanced"
    ),
    "svm": SVC(class_weight="balanced"),
}


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

    def getNumberofClasses(self):
        """

        :return: Get the number of classes (i.e. number of roof types)
        :rtype: int
        """
        roofingShapefileDir = self.dlg.lineEdit_2.text()
        shpFolder = Path(roofingShapefileDir).rglob("*.shp")
        files = [shp for shp in shpFolder]
        return len(files)

    def convertRaster2Array(rasterFilepath):
        """Convert a multiband raster into a numpy array.
        Given a 3-band raster image of size ncols*nrows pixels, the function will return
        an numpy array of shape (3, ncols, nrows).

        :param rasterFilepath: Filepath of the raster to convert
        :type rasterFilepath: str
        :return: Converted image into array
        :rtype: numpy.array
        """
        raster_dataset = gdal.Open(rasterFilepath, gdal.GA_ReadOnly)
        bands_data = []
        # Parsing the raster's bands
        for b in range(1, raster_dataset.RasterCount + 1):
            band = raster_dataset.GetRasterBand(b)
            bands_data.append(band.ReadAsArray())
        # Create an array of shape (ndim, nrows, ncols)
        bands_data = np.dstack(bands_data)
        return bands_data

    def rasterizeRoofingLayer(vectorFilepath, rasterFilepath, classNumber):
        """Rasterizing a vector layer into a raster layer.
        The image pixels which account for the vector elements are labelled with the input class number value.
        The output image dimension is the same as the image raster to be classified.
        This function will be run to rasterize roofing layers.
        We assume that both raster and vector layers have the same SCR.

        :param vectorFilepath: Path to vector layer
        :type vectorFilepath: str
        :param classNumber: The value that will account for each rasterized element.
                            For instance, if classNumber = 5, then the rasterized elements
                            cells of the output output will value 5.
        :type classNumber: int
        :return: Rasterized roofing filepath.
        :rtype: str
        """

        vlayer = QgsVectorLayer(vectorFilepath, "roofing", "ogr")
        rlayer = QgsRasterLayer(rasterFilepath, "inputRaster")
        params = {
            "INPUT": vlayer,
            "BURN": classNumber,
            "UNITS": 1,  # Georeferecend pixels,
            "DATA_TYPE": 2,  # UInt16 data type
            "WIDTH": rlayer.rasterUnitsPerPixelX(),  # Using input raster resolution
            "HEIGHT": rlayer.rasterUnitsPerPixelY(),
            "EXTENT": rlayer.id(),
            "OUTPUT": "TEMPORARY_OUTPUT",
        }
        rasterizedRoofing = processing.run("gdal:rasterize", params)
        return rasterizedRoofing["OUTPUT"]

    def labellingRoofingRaster(roofingShapefileDir, rasterFilepath):
        """Generating a raster in which all the roofs are labelled by type.

        :param roofingShapefileDir: Roofing layers directory (it contains one shapefile per type of roof)
        :type roofingShapefileDir: str
        :param rasterFilepath: Filepath of the raster image to be classified
        :type rasterFilepath: str
        :return: A raster image in which the roofs are labelled according to their type.
        :rtype: np.array
        """
        rlayer = QgsRasterLayer(rasterFilepath, "inputRaster")
        # The output image has the same dimension as the input raster layer
        labelledImg = np.zeros((rlayer.width(), rlayer.height()))

        shpFolder = Path(roofingShapefileDir).rglob("*.shp")
        files = [x for x in shpFolder]
        for classLabel, roofVectorFilepath in enumerate(files, start=1):
            tempRasterFile = RoofClassify.rasterizeRoofingLayer(
                roofVectorFilepath, rasterFilepath, classLabel
            )
            # Read the roof rasterized file, and convert the first raster band into a numpy array
            roofLabelledRaster = (
                gdal.Open(tempRasterFile).GetRasterBand(1).ReadAsArray()
            )
            labelledImg += roofLabelledRaster
        return labelledImg

    def writeGeotiff(inputImgFile, classifiedImg, roofTypesNumber, outputImgfilepath):
        """Write an numpy array image into a geotiff image.

        :param inputImgFile: Filepath of the input raster image before classification.
                            Its spatial properties will be copied into the output geotiff image.
        :type inputImgFile: str
        :param classifiedImg: Classified image
        :type classifiedImg: numpy.array
        :param roofTypesNumber: Number of classes i.e. number of roof types used in the classification
        :type roofTypesNumber: int
        :param outputImgfilepath: Filepath of the output geotiff image
        :type outputImgfilepath: str
        :return: Converted raster into geotiff image
        :rtype: QgsRasterLayer
        """
        inputRaster = gdal.Open(inputImgFile)
        driver = gdal.GetDriverByName("GTiff")
        rows, cols = classifiedImg.shape
        dataset = driver.Create(outputImgfilepath, cols, rows, 1, gdal.GDT_Byte)
        dataset.SetGeoTransform(inputRaster.GetGeoTransform())
        dataset.SetProjection(inputRaster.GetProjectionRef())
        band = dataset.GetRasterBand(1)
        band.WriteArray(classifiedImg)

        # Create a pseudo-color table for the first band
        pct = gdal.ColorTable()
        for classLabel in range(roofTypesNumber + 1):
            color_hex = COLORS[classLabel]
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            pct.SetColorEntry(classLabel, (r, g, b, 255))
        band.SetColorTable(pct)

        # Add metadata to the first image
        metadata = {
            "TIFFTAG_COPYRIGHT": "CC BY 4.0",
            "TIFFTAG_DOCUMENTNAME": "classification",
            "TIFFTAG_IMAGEDESCRIPTION": "Supervised classification.",
            "TIFFTAG_MAXSAMPLEVALUE": str(roofTypesNumber),
            "TIFFTAG_MINSAMPLEVALUE": "0",
            "TIFFTAG_SOFTWARE": "Python, GDAL, scikit-learn",
        }
        dataset.SetMetaData(metadata)
        rlayer = QgsRasterLayer(outputImgfilepath, "classifiedImg")
        return rlayer

    def mergeRasterLayers(rasterLayerList, outputDirectory):
        """Merging classified images into one image. The merged image is saved under the name
        'merged_classification.tif'.

        :param rasterLayerList: List of classified images
        :type rasterLayerList: list<QgsRasterLayer>
        :param outputDirectory: output directory
        :type outputDirectory: str
        """
        mergeParams = {
            "DATA_TYPE": 2,  # UInt16 encoded output
            "EXTRA": "",
            "INPUT": rasterLayerList,
            "NODATA_INPUT": None,
            "NODATA_OUTPUT": None,
            "OPTIONS": "",
            "OUTPUT": f"{outputDirectory}merged_classification.tif",
            "PCT": True,  # Grab a pseudo-color table from the first input image
            "SEPARATE": False,
        }
        processing.run("gdal:merge", mergeParams)

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            self.log(self.dlg.lineEdit.text())
            self.log(self.dlg.lineEdit_2.text())
            directory_raster = self.dlg.lineEdit.text()
            directory_shape = self.dlg.lineEdit_2.text()
            raster_training = self.dlg.lineEdit_3.text()
            os.chdir(directory_raster)
            self.log(raster_training)
            out_folder = self.dlg.lineEdit_4.text()

            # Training data processing
            raster_dataset = gdal.Open(raster_training, gdal.GA_ReadOnly)
            bands_data = []
            for b in range(1, raster_dataset.RasterCount + 1):
                band = raster_dataset.GetRasterBand(b)
                bands_data.append(band.ReadAsArray())

            bands_data = np.dstack(bands_data)
            rows, cols, n_bands = bands_data.shape

            # Labelling the training image
            labeled_pixels = RoofClassify.labellingRoofingRaster(
                directory_shape, raster_training
            )
            is_train = np.nonzero(labeled_pixels)
            training_labels = labeled_pixels[is_train]
            training_samples = bands_data[is_train]
            # Creating and training the classifier with labelled data
            classifier = CLASSIFIERS["random-forest"]

            classifier.fit(training_samples, training_labels)

            classifiedImages = []
            for file in glob.glob("*.tif"):
                self.log(file)

                x = directory_raster + "/" + file
                self.log(x)
                raster_dataset2 = gdal.Open(x, gdal.GA_ReadOnly)
                bands_data2 = []
                for b in range(1, raster_dataset2.RasterCount + 1):
                    band2 = raster_dataset2.GetRasterBand(b)
                    bands_data2.append(band2.ReadAsArray())
                bands_data2 = np.dstack(bands_data2)
                rows2, cols2, n_bands2 = bands_data2.shape

                n_samples2 = rows2 * cols2

                flat_pixels = bands_data2.reshape((n_samples2, n_bands2))

                result = classifier.predict(flat_pixels)

                # Reshape the result: split the labeled pixels into rows to create an image
                classification = result.reshape((rows2, cols2))
                file = file.replace(".tif", "")
                name = out_folder + "\\" + file + "_classificato.tif"
                self.log(name)
                # Write the image array into a QgsRasterLayer
                rasterOutput = RoofClassify.writeGeotiff(
                    x, classification, self.getNumberofClasses(), name
                )
                classifiedImages.append(rasterOutput)

            RoofClassify.mergeRasterLayers(classifiedImages, out_folder)
