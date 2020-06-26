# Asbestos Roof Classification Plugin

A QGIS tool that is conceived for automatically identifying buildings with asbestos roofing. Its task is to identify asbestos cladding in remotely sensed images. For more detailed informations on how it works refer to the article: [A QGIS Tool for Automatically Identifying Asbestos Roofing](https://www.mdpi.com/2220-9964/8/3/131) (https://doi.org/10.3390/ijgi8030131)

Version 1.0 - March 2019

GNU General Public License version 2 or later

## Dependencies

This plugin requires:
 
 - The Python Shapefile Library (PyShp)
      * `pip install pyshp`
 - scikit-learn
      * `pip install sklearn`

## Quick start Guide

Go to `Plugins` -> `Manage and Install Plugins`, look for "ClassifyRoofs" Locator and install the plugin.

Open the plugins GUI by clicking to its icon or from the  plugin menu entry `Plugins`-> `ClassifyRoofs`.
               ![gui](https://github.com/SatStatPIN/RoofClassify/blob/master/img/gui.png)

Fill the entries with the requested paths and click `ok`

## NOTES

The images for testing this software are big in size and costly, so if problems are encountered using your own data please feel free to contact [at this address](arjan.feta@stud.unifi.it).
