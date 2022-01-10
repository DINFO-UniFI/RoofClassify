# Installation

## Requirements

- {{ qgis_version_min }}  < QGIS < {{ qgis_version_max }}
- Python 3.7+
- dependencies listed in `requirements/embedded.txt`:
  - embedded on Windows version
  - on Linux, you need to install by yourself. Typically, on Ubuntu:

```bash
python3 -m pip -U -r requirements/embedded.txt
```

## Stable version (recomended)

This plugin is published on the official QGIS plugins repository: <https://plugins.qgis.org/plugins/RoofClassify/>.

Go to `Plugins` -> `Manage and Install Plugins`, look for "ClassifyRoofs" and install the plugin.

## Beta versions released

Enable experimental extensions in the QGIS plugins manager settings panel.
