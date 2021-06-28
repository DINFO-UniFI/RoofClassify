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
import subprocess

# 3rd party
import numpy as np

# Initialize Qt resources from file resources.py
from osgeo import gdal
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog

# Import the code for the dialog
from roof_classify_dialog import RoofClassifyDialog
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

from roof_classify.__about__ import DIR_PLUGIN_ROOT, __title__
from roof_classify.toolbelt import PlgLogger

#creo un set di colori pseudocasuali da usare poi nella classificazione
COLORS = [
    "#000000", "#FFFF00", "#1CE6FF", "#FF34FF", "#FF4A46", "#008941", "#006FA6", "#A30059",
    "#FFDBE5", "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#004D43", "#8FB0FF", "#997D87",
    "#5A0007", "#809693", "#FEFFE6", "#1B4400", "#4FC601", "#3B5DFF", "#4A3B53", "#FF2F80",
    "#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B903AA", "#D16100",
    "#DDEFFF", "#000035", "#7B4F4B", "#A1C299", "#300018", "#0AA6D8", "#013349", "#00846F",
    "#372101", "#FFB500", "#C2FFED", "#A079BF", "#CC0744", "#C0B9B2", "#C2FF99", "#001E09",
    "#00489C", "#6F0062", "#0CBD66", "#EEC3FF", "#456D75", "#B77B68", "#7A87A1", "#788D66",
    "#885578", "#FAD09F", "#FF8A9A", "#D157A0", "#BEC459", "#456648", "#0086ED", "#886F4C",
    "#34362D", "#B4A8BD", "#00A6AA", "#452C2C", "#636375", "#A3C8C9", "#FF913F", "#938A81",
    "#575329", "#00FECF", "#B05B6F", "#8CD0FF", "#3B9700", "#04F757", "#C8A1A1", "#1E6E00",
    "#7900D7", "#A77500", "#6367A9", "#A05837", "#6B002C", "#772600", "#D790FF", "#9B9700",
    "#549E79", "#FFF69F", "#201625", "#72418F", "#BC23FF", "#99ADC0", "#3A2465", "#922329",
    "#5B4534", "#FDE8DC", "#404E55", "#0089A3", "#CB7E98", "#A4E804", "#324E72", "#6A3A4C",
    "#83AB58", "#001C1E", "#D1F7CE", "#004B28", "#C8D0F6", "#A3A489", "#806C66", "#222800",
    "#BF5650", "#E83000", "#66796D", "#DA007C", "#FF1A59", "#8ADBB4", "#1E0200", "#5B4E51",
    "#C895C5", "#320033", "#FF6832", "#66E1D3", "#CFCDAC", "#D0AC94", "#7ED379", "#012C58"
]


def calcolaMedia(mat,i,dim) :
    num_val=0
    somma=0
    for j in range(dim-1) :
        if mat[j,i] != 0 :
            num_val=num_val+1
            somma=somma+mat[j,i]
    return somma/num_val ,num_val









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
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'RoofClassify_{}.qm'.format(locale))

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
        parent=None):
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
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = str(DIR_PLUGIN_ROOT / "resources/images/icon.png")
        self.add_action(
            icon_path,
            text=self.tr(u'classify roofs'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                __title__,
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def select_raster(self):       # cartella che contiene i raster da dover classificare
        #filename = QFileDialog.getOpenFileName(self.dlg, "Select raster ","", '*.tif')
        directory=QFileDialog.getExistingDirectory(self.dlg, "Seleziona cartella contenente raster da classificare")
        #self.dlg.lineEdit.setText(filename)
        self.dlg.lineEdit.setText(directory)


    def select_shape(self):
        #filename=QFileDialog.getOpenFileName(self.dlg, "select shape","",'*.shp')
        #self.dlg.lineEdit_2.setText(filename)
        directory2=QFileDialog.getExistingDirectory(self.dlg, "Seleziona cartella contenente shape di training")
        self.dlg.lineEdit_2.setText(directory2)


    def select_raster_class(self):
        filename=QFileDialog.getOpenFileName(self.dlg, "select training raster","",'*.tif')
        self.dlg.lineEdit_3.setText(filename)

    def select_output_folder(self):
        out_folder=QFileDialog.getExistingDirectory(self.dlg, "Seleziona cartella per output")
        self.dlg.lineEdit_4.setText(out_folder)



    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:

            # da qui inizia l'esecuzione del plugin una volta che si preme OK


            # serve per rasterizzare un vettore. Ritorna un gdal.Dataset.
            def create_mask_from_vector(vector_data_path, cols, rows, geo_transform, projection, target_value=1,
                                        output_fname='', dataset_format='MEM'):
                """
                :param vector_data_path: Path ad un shapefile
                :param cols: Numero di colonne del risultato
                :param rows: Numero di righe del risultato
                :param geo_transform: Returned value of gdal.Dataset.GetGeoTransform (coefficients for
                                      transforming between pixel/line (P,L) raster space, and projection
                                      coordinates (Xp,Yp) space.
                :param projection: Projection definition string (Returned by gdal.Dataset.GetProjectionRef)
                :param target_value: Pixel value for the pixels. Must be a valid gdal.GDT_UInt16 value.
                :param output_fname: If the dataset_format is GeoTIFF, this is the output file name
                :param dataset_format: The gdal.Dataset driver name. [default: MEM]
                """
                data_source = gdal.OpenEx(vector_data_path, gdal.OF_VECTOR)
                if data_source is None:
                    self.log(message=f"File read failed: {vector_data_path}", log_level=2, push=True)
                layer = data_source.GetLayer(0)
                driver = gdal.GetDriverByName(dataset_format)
                target_ds = driver.Create(output_fname, cols, rows, 1, gdal.GDT_UInt16)
                target_ds.SetGeoTransform(geo_transform)
                target_ds.SetProjection(projection)
                gdal.RasterizeLayer(target_ds, [1], layer, burn_values=[target_value])
                return target_ds


            def vectors_to_raster(file_paths, rows, cols, geo_transform, projection):
                """
                Rasterize, in a single image, all the vectors in the given directory.
                The data of each file will be assigned the same pixel value. This value is defined by the order
                of the file in file_paths, starting with 1: so the points/poligons/etc in the same file will be
                marked as 1, those in the second file will be 2, and so on.
                :param file_paths: Path to a directory with shapefiles
                :param rows: Number of rows of the result
                :param cols: Number of columns of the result
                :param geo_transform: Returned value of gdal.Dataset.GetGeoTransform (coefficients for
                                      transforming between pixel/line (P,L) raster space, and projection
                                      coordinates (Xp,Yp) space.
                :param projection: Projection definition string (Returned by gdal.Dataset.GetProjectionRef)
                """
                labeled_pixels = np.zeros((rows, cols))
                for i, path in enumerate(file_paths):
                    label = i+1

                    ds = create_mask_from_vector(path, cols, rows, geo_transform, projection,
                                                 target_value=label)
                    band = ds.GetRasterBand(1)
                    a = band.ReadAsArray()

                    labeled_pixels += a
                    ds = None
                return labeled_pixels



            def write_geotiff(fname, data, geo_transform, projection, data_type=gdal.GDT_Byte):
                """
                Create a GeoTIFF file with the given data.
                :param fname: Path to a directory with shapefiles
                :param data: Number of rows of the result
                :param geo_transform: Returned value of gdal.Dataset.GetGeoTransform (coefficients for
                                      transforming between pixel/line (P,L) raster space, and projection
                                      coordinates (Xp,Yp) space.
                :param projection: Projection definition string (Returned by gdal.Dataset.GetProjectionRef)
                """
                driver = gdal.GetDriverByName('GTiff')
                rows, cols = data.shape
                dataset = driver.Create(fname, cols, rows, 1, data_type)
                dataset.SetGeoTransform(geo_transform)
                dataset.SetProjection(projection)
                band = dataset.GetRasterBand(1)
                band.WriteArray(data)

                ct = gdal.ColorTable()
                for pixel_value in range(len(classes)+1):
                    color_hex = COLORS[pixel_value]
                    r = int(color_hex[1:3], 16)
                    g = int(color_hex[3:5], 16)
                    b = int(color_hex[5:7], 16)
                    ct.SetColorEntry(pixel_value, (r, g, b, 255))
                band.SetColorTable(ct)

                metadata = {
                    'TIFFTAG_COPYRIGHT': 'CC BY 4.0',
                    'TIFFTAG_DOCUMENTNAME': 'classification',
                    'TIFFTAG_IMAGEDESCRIPTION': 'Supervised classification.',
                    'TIFFTAG_MAXSAMPLEVALUE': str(len(classes)),
                    'TIFFTAG_MINSAMPLEVALUE': '0',
                    'TIFFTAG_SOFTWARE': 'Python, GDAL, scikit-learn'
                }
                dataset.SetMetadata(metadata)

                dataset = None  # Close the file
                return







            self.log(self.dlg.lineEdit.text())
            self.log(self.dlg.lineEdit_2.text())
            #rasterIn=self.dlg.lineEdit.text()
            directory_raster=self.dlg.lineEdit.text()
            directory_shape=self.dlg.lineEdit_2.text()
            raster_training=self.dlg.lineEdit_3.text()
            #log = open("D:/AMIANTO/output/log.txt", "w")
            os.chdir(directory_raster)
            self.log(raster_training)
            #log.write(time.strftime("%Y-%m-%d %H:%M"))
            #log.write("caricamento training set..\n")
            out_folder=self.dlg.lineEdit_4.text()



            nomi=""


            nnn=1
            for file in glob.glob("*.tif"):
                self.log(file)
                #raster_dataset2 = gdal.Open("C:/Users/Alessandro/Desktop/11-10/ViaToscanaTestRitagliato.tif", gdal.GA_ReadOnly)

                x=directory_raster+'/'+file
                self.log(x)
                raster_dataset2 = gdal.Open(x, gdal.GA_ReadOnly)


                geo_transform2 = raster_dataset2.GetGeoTransform()


                proj2 = raster_dataset2.GetProjectionRef()
                bands_data2 = []
                for b in range(1, raster_dataset2.RasterCount+1):
                        band2 = raster_dataset2.GetRasterBand(b)
                        bands_data2.append(band2.ReadAsArray())
                bands_data2 = np.dstack(bands_data2)
                rows2, cols2, n_bands2 = bands_data2.shape

                n_samples2 = rows2*cols2


                raster_dataset = gdal.Open(raster_training, gdal.GA_ReadOnly)
                geo_transform = raster_dataset.GetGeoTransform()
                proj = raster_dataset.GetProjectionRef()
                bands_data = []
                for b in range(1, raster_dataset.RasterCount+1):
                        band = raster_dataset.GetRasterBand(b)
                        bands_data.append(band.ReadAsArray())

                bands_data = np.dstack(bands_data)
                rows, cols, n_bands = bands_data.shape




                    # A sample is a vector with all the bands data. Each pixel (independent of its position) is a
                    # sample.
                n_samples = rows*cols
                files = [f for f in os.listdir(directory_shape) if f.endswith('.shp')]

                classes = [f.split('.')[0] for f in files]
                self.log(str(classes))
                shapefiles = [os.path.join(directory_shape, f) for f in files if f.endswith('.shp')]
                labeled_pixels = vectors_to_raster(shapefiles, rows, cols, geo_transform, proj)
                is_train = np.nonzero(labeled_pixels)
                training_labels = labeled_pixels[is_train]
                training_samples = bands_data[is_train]

                flat_pixels = bands_data2.reshape((n_samples2, n_bands2))

                CLASSIFIERS = {
                        # http://scikit-learn.org/dev/modules/generated/sklearn.ensemble.RandomForestClassifier.html
                        'random-forest': RandomForestClassifier(n_jobs=4, n_estimators=10, class_weight='balanced'),
                        # http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html
                        'svm': SVC(class_weight='balanced')
                }
                classifier = CLASSIFIERS['random-forest']

                classifier.fit(training_samples, training_labels)


                result = classifier.predict(flat_pixels)

                    # Reshape the result: split the labeled pixels into rows to create an image
                classification = result.reshape((rows2, cols2))
                file=file.replace(".tif","")
                name=out_folder+"\\"+file+"_classificato.tif"
                self.log(name)
                write_geotiff(name, classification, geo_transform2, proj2)
                nnn=nnn+1
                nomi = nomi + " " + name


            if nnn>2:
                dove= "D:/risultato/ClassificataUnita.tif"
                subprocess.call("gdal_merge.bat -ot UInt16 -pct -o "+dove+" -of GTiff " + nomi)

            if self.dlg.checkBox.isChecked():
                self.log("ciao")
                #inserire codice che crea shape conteggio
            if self.dlg.checkBox_2.isChecked():
                self.log("ciao2")
                #inserire codice che crea shape percentuale
