#! python3  # noqa: E265

# 3rd party
import numpy
from osgeo import gdal

# ############################################################################
# ########## Classes ###############
# ##################################


class DataClassifier:
    """Data processing and classifiers."""

    def __init__(self) -> None:
        self.CLASSIFIERS: dict = {}

    def classifyRoofTypes(trainedClassifier, rasterFilepath):
        """Classify roofs in a raster image using a trained classifier.

        :param trainedClassifier: A trained ramdom forest classifier
        :type trainedClassifier: sklearn.ensemble.RandomForestClassifier
        :param rasterFilepath: Raster image filepath
        :type rasterFilepath: str
        :return: Classified raster image
        :rtype: np.ndarray
        """
        imgArray = self.convertRaster2Array(rasterFilepath)
        nrows, ncols, nbands = imgArray.shape
        ncells = nrows * ncols
        # Flattening the raster image to fit with the classifier predict function
        flatImg = imgArray.reshape((ncells, nbands))
        result = trainedClassifier.predict(flatImg)
        # Reshape the result: split the labeled pixels into rows to create an image
        classifiedImg = result.reshape((nrows, ncols))
        return classifiedImg

    def convertRaster2Array(self, rasterFilepath) -> numpy.array:
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
        # Create an array of shape (nrows, ncols, ndim)
        bands_data = numpy.dstack(bands_data)
        return bands_data

    def generateTrainingData(trainingRasterFilepath, shapefilesDirectory):
        """Generate training data for roof classification.

        :param trainingRasterFilepath: Training raster filepath
        :type trainingRasterFilepath: str
        :param shapefilesDirectory: Directory that contains the roof shapefiles
                                    (one file per roof type)
        :type shapefilesDirectory: str
        :return: A set of roof pixels and their corresponding label (i.e their type of roof)
        :rtype: (np.ndarray, np.ndarray)
        """
        # Training data processing
        trainingImgArray = self.convertRaster2Array(trainingRasterFilepath)

        # Labelling the training image
        labelledImg = self.labellingRoofingRaster(
            shapefilesDirectory, trainingRasterFilepath
        )
        roofPixelIdx = numpy.nonzero(labelledImg)  # Pixel indice of the roofs
        pixelsLabel = labelledImg[roofPixelIdx]
        pixelsValue = trainingImgArray[roofPixelIdx]
        return pixelsValue, pixelsLabel


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    classif_tools = DataClassifier()
