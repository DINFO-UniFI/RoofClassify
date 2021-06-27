# Asbestos Roof Classification Plugin

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![flake8](https://img.shields.io/badge/linter-flake8-green)](https://flake8.pycqa.org/)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

[![Documentation Builder](https://github.com/DINFO-UniFI/RoofClassify/actions/workflows/docs_builder.yml/badge.svg)](https://dinfo-unifi.github.io/RoofClassify/)
[![Tester](https://github.com/DINFO-UniFI/RoofClassify/actions/workflows/tester.yml/badge.svg)](https://github.com/DINFO-UniFI/RoofClassify/actions/workflows/tester.yml)
[![Packager](https://github.com/DINFO-UniFI/RoofClassify/actions/workflows/packager.yml/badge.svg)](https://github.com/DINFO-UniFI/RoofClassify/actions/workflows/packager.yml)
[![Releaser](https://github.com/DINFO-UniFI/RoofClassify/actions/workflows/release.yml/badge.svg)](https://github.com/DINFO-UniFI/RoofClassify/actions/workflows/release.yml)

A QGIS tool that is conceived for automatically identifying buildings with asbestos roofing. Its task is to identify asbestos cladding in remotely sensed images. For more detailed informations on how it works refer to the article: [A QGIS Tool for Automatically Identifying Asbestos Roofing](https://www.mdpi.com/2220-9964/8/3/131) (https://doi.org/10.3390/ijgi8030131)

## Dependencies

This plugin requires:

- The Python Shapefile Library (PyShp)
  - `pip install pyshp`
- scikit-learn
  - `pip install sklearn`



## NOTES

The images for testing this software are big in size and costly, so if problems are encountered using your own data please feel free to contact [at this address](arjan.feta@stud.unifi.it).

## Documentation

The technical and user documentation is here: <https://dinfo-unifi.github.io/RoofClassify/>

----

## License

The project license is [GPLv2+](LICENSE).
