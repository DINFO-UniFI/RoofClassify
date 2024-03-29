#! python3  # noqa: E265

"""
    Main plugin module.
"""

# standard
import os.path
from functools import partial
from pathlib import Path

# Initialize Qt resources from file resources.py
from qgis.core import QgsApplication, QgsSettings
from qgis.PyQt.Qt import QUrl
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog

# Import the code for the dialog
from RoofClassify.__about__ import (
    DIR_PLUGIN_ROOT,
    __icon_path__,
    __title__,
    __uri_homepage__,
)
from RoofClassify.gui.dlg_settings import PlgOptionsFactory
from RoofClassify.gui.roof_classify_dialog import RoofClassifyDialog

try:
    from RoofClassify.logic import DataClassifier
except ImportError:
    DataClassifier = None
from RoofClassify.toolbelt import PlgLogger


class RoofClassifyPlugin:
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

        # initialize locale
        locale: str = QgsSettings().value("locale/userLocale", QLocale().name())[0:2]
        locale_path: Path = DIR_PLUGIN_ROOT / f"resources/i18n/{__title__}_{locale}.qm"

        if locale_path.exists():
            self.translator = QTranslator()
            self.translator.load(str(locale_path.resolve()))
            QCoreApplication.installTranslator(self.translator)
            self.log(message=f"DEBUG: Translation used: {locale_path}", log_level=4)

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

    def check_dependencies(self) -> None:
        """Check if all dependencies are satisfied. If not, warn the user and disable plugin."""
        # if import failed
        if DataClassifier is None:
            self.log(
                message=self.tr("Error importing Scikit Learn. Plugin disabled."),
                log_level=2,
                push=True,
                button=True,
                button_connect=partial(
                    QDesktopServices.openUrl,
                    QUrl(f"{__uri_homepage__}/usage/installation"),
                ),
                button_text=self.tr("Installation instructions"),
                duration=0,
            )
            for action in self.actions:
                action.setEnabled(False)
        else:
            self.log(message=self.tr("Dependencies satisfied"), log_level=4)
            for action in self.actions:
                action.setEnabled(True)

    def tr(self, message: str) -> str:
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: str
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

        # settings page within the QGIS preferences menu
        self.options_factory = PlgOptionsFactory()
        self.iface.registerOptionsWidgetFactory(self.options_factory)

        self.add_action(
            str(__icon_path__),
            text=self.tr("Launch classification"),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

        self.add_action(
            icon_path=QgsApplication.iconPath("console/iconSettingsConsole.svg"),
            text=self.tr("Settings"),
            callback=lambda: self.iface.showOptionsDialog(
                currentPage="mOptionsPage{}".format(__title__)
            ),
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
        )

        # -- Post UI initialization
        # self.iface.initializationCompleted.connect(self.check_dependencies)
        self.check_dependencies()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(__title__, action)
            self.iface.removeToolBarIcon(action)

        # -- Clean up preferences panel in QGIS settings
        self.iface.unregisterOptionsWidgetFactory(self.options_factory)

        # remove the toolbar
        del self.toolbar

    def select_raster(self):  # cartella che contiene i raster da dover classificare
        # filename = QFileDialog.getOpenFileName(self.dlg, "Select raster ","", '*.tif')
        directory = QFileDialog.getExistingDirectory(
            self.dlg, "Select folder containing raster(s) to be classified"
        )
        # self.dlg.lineEdit.setText(filename)
        self.dlg.lineEdit.setText(directory)

    def select_shape(self):
        # filename=QFileDialog.getOpenFileName(self.dlg, "select shape","",'*.shp')
        # self.dlg.lineEdit_2.setText(filename)
        directory2 = QFileDialog.getExistingDirectory(
            self.dlg, "Select folder containing training layers"
        )
        self.dlg.lineEdit_2.setText(directory2)

    def select_raster_class(self):
        filename = QFileDialog.getOpenFileName(
            self.dlg, "Select training raster", "", "*.tif"
        )[0]
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

            # Link class labels to roof types
            DataClassifier.write_link_classlabel_roof_shp(shapefilesDirectory)

            classifiedImages = []
            # Parsing the images to be classified
            for file in Path(rasterDirectory).rglob("*.tif"):
                imgFilepath = str(file)
                self.log(imgFilepath)
                # Classify the image
                classifiedImage = classifier.classifyRoofTypes(imgFilepath)
                # Define an export filepath for the classified image
                outputFilename = (file.name).replace(".tif", "_classsified.tif")
                outputFilepath = "/".join((outputDirectory, outputFilename))
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
