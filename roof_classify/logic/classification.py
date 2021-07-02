#! python3  # noqa: E265

# 3rd party
from typing import List

import numpy
from osgeo import gdal

try:
    from sklearn.ensemble import RandomForestClassifier
except Exception:
    import site

    from roof_classify.__about__ import DIR_PLUGIN_ROOT

    site.addsitedir(DIR_PLUGIN_ROOT / "embedded_external_libs")
    from roof_classify.embedded_external_libs.sklearn.ensemble import (
        RandomForestClassifier,
    )

from pathlib import Path

from qgis import processing
from qgis.core import QgsRasterLayer, QgsVectorLayer

# ############################################################################
# ########## Classes ###############
# ##################################

# fmt: off
# Set of colors to create a pseudo-color table used in the classification
COLORS = (
    "#000000", "#FFFF00", "#1CE6FF", "#FF34FF", "#FF4A46", "#008941", "#006FA6", 
    "#A30059", "#FFDBE5", "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#004D43", 
    "#8FB0FF", "#997D87", "#5A0007", "#809693", "#FEFFE6", "#1B4400", "#4FC601",
    "#3B5DFF", "#4A3B53", "#FF2F80", "#61615A", "#BA0900", "#6B7900", "#00C2A0",
    "#FFAA92", "#FF90C9", "#B903AA", "#D16100", "#DDEFFF", "#000035", "#7B4F4B",
    "#A1C299", "#300018", "#0AA6D8", "#013349", "#00846F", "#372101", "#FFB500",
    "#C2FFED", "#A079BF", "#CC0744", "#C0B9B2", "#C2FF99", "#001E09", "#00489C",
    "#6F0062", "#0CBD66", "#EEC3FF", "#456D75", "#B77B68", "#7A87A1", "#788D66",
    "#885578", "#FAD09F", "#FF8A9A", "#D157A0", "#BEC459", "#456648", "#0086ED", 
    "#886F4C", "#34362D", "#B4A8BD", "#00A6AA", "#452C2C", "#636375", "#A3C8C9",
    "#FF913F", "#938A81", "#575329", "#00FECF", "#B05B6F", "#8CD0FF", "#3B9700",
    "#04F757", "#C8A1A1", "#1E6E00", "#7900D7", "#A77500", "#6367A9", "#A05837",
    "#6B002C", "#772600", "#D790FF", "#9B9700", "#549E79", "#FFF69F", "#201625",
    "#72418F", "#BC23FF", "#99ADC0", "#3A2465", "#922329", "#5B4534", "#FDE8DC",
    "#404E55", "#0089A3", "#CB7E98", "#A4E804", "#324E72", "#6A3A4C", "#83AB58",
    "#001C1E", "#D1F7CE", "#004B28", "#C8D0F6", "#A3A489", "#806C66", "#222800",
    "#BF5650", "#E83000", "#66796D", "#DA007C", "#FF1A59", "#8ADBB4", "#1E0200",
    "#5B4E51", "#C895C5", "#320033", "#FF6832", "#66E1D3", "#CFCDAC", "#D0AC94",
    "#7ED379", "#012C58"
)
# fmt: on


class DataClassifier:
    """Data processing and classifiers."""

    def __init__(self) -> None:
        self.classifier = RandomForestClassifier(
            n_jobs=4, n_estimators=10, class_weight="balanced"
        )

    def classifyRoofTypes(self, rasterFilepath: str) -> numpy.array:
        """Classify roofs in a raster image using a trained classifier.

        :param rasterFilepath: Raster image filepath
        :type rasterFilepath: str
        :return:  Classified raster image
        :rtype: numpy.array
        """

        imgArray = self.convertRaster2Array(rasterFilepath)
        nrows, ncols, nbands = imgArray.shape
        ncells = nrows * ncols
        # Flattening the raster image to fit with the classifier predict function
        flatImg = imgArray.reshape((ncells, nbands))
        result = self.classifier.predict(flatImg)
        # Reshape the result: split the labeled pixels into rows to create an image
        classifiedImg = result.reshape((nrows, ncols))
        return classifiedImg

    def train(self, trainingRasterFilepath: str, shapefilesDirectory: str):
        # Training data processing
        trainingImgArray = DataClassifier.convertRaster2Array(trainingRasterFilepath)

        # Labelling the training image
        labelledImg = self.labellingRoofingRaster(
            shapefilesDirectory, trainingRasterFilepath
        )
        roofPixelIdx = numpy.nonzero(labelledImg)  # Pixel indice of the roofs
        pixelsLabel = labelledImg[roofPixelIdx]
        pixelsValue = trainingImgArray[roofPixelIdx]
        self.classifier.fit(pixelsValue, pixelsLabel)

    @staticmethod
    def convertRaster2Array(rasterFilepath: str) -> numpy.array:
        """Convert a multiband raster into a numpy array.
        Given a 3-band raster image of size ncols*nrows pixels, the function will return
        an numpy array of shape (ncols, nrows, 3).

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
        # Create an array of shape (nrows, ncols, ndim)
        bands_data = numpy.dstack(bands_data)
        return bands_data

    @staticmethod
    def labellingRoofingRaster(
        roofingShapefileDir: str, rasterFilepath: str
    ) -> numpy.array:
        """Generating a raster in which all the roofs are labelled by type.

        :param roofingShapefileDir: Roofing layers directory (it contains one shapefile
                                    per type of roof)
        :type roofingShapefileDir: str
        :param rasterFilepath: Filepath of the raster image to be classified
        :type rasterFilepath: str
        :return: A raster image in which the roofs are labelled according to their type.
        :rtype: numpy.array
        """
        rlayer = QgsRasterLayer(rasterFilepath, "inputRaster")
        # The output image has the same dimension as the input raster layer
        labelledImg = numpy.zeros((rlayer.width(), rlayer.height()))

        shpFolder = Path(roofingShapefileDir).rglob("*.shp")
        files = [x for x in shpFolder]
        for classLabel, roofVectorFilepath in enumerate(files, start=1):
            tempRasterFile = DataClassifier.rasterizeRoofingLayer(
                roofVectorFilepath, rasterFilepath, classLabel
            )
            # Read the roof rasterized file, and convert the first raster band into a numpy array
            roofLabelledRaster = (
                gdal.Open(tempRasterFile).GetRasterBand(1).ReadAsArray()
            )
            labelledImg += roofLabelledRaster
        return labelledImg

    @staticmethod
    def rasterizeRoofingLayer(
        vectorFilepath: str, rasterFilepath: str, classNumber: int
    ) -> str:
        """Rasterizing a vector layer into a raster layer.
        The image pixels which account for the vector elements are labelled with the input
        class number value.
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

    @staticmethod
    def writeGeotiff(
        inputImgFile: str,
        classifiedImg: numpy.array,
        roofTypesNumber: int,
        outputImgfilepath: str,
    ) -> QgsRasterLayer:
        """Write an numpy array image into a geotiff image.

        :param inputImgFile: Filepath of the input raster image before classification.
                            Its spatial properties will be copied into the output geotiff image.
        :type inputImgFile: str
        :param classifiedImg: Classified image
        :type classifiedImg: numpy.array
        :param roofTypesNumber: Number of classes i.e. number of roof types used in the
                                classification
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

    @staticmethod
    def mergeRasterLayers(rasterLayerList: List[QgsRasterLayer], outputDirectory: str):
        """Merging classified images into one image. The merged image is saved under the name
        'merged_classification.tif'.

        :param rasterLayerList: List of classified images
        :type rasterLayerList: list(QgsRasterLayer)
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
            "OUTPUT": f"{outputDirectory}_merged_classification.tif",
            "PCT": True,  # Grab a pseudo-color table from the first input image
            "SEPARATE": False,
        }
        processing.run("gdal:merge", mergeParams)


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    classif_tools = DataClassifier()
