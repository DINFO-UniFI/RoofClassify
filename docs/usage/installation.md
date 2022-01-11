# Installation

## Requirements

The plugin's logic is mainly based on well-known machine learning kit: [scikit-learn](https://scikit-learn.org/stable/). To work, the plugin needs it and it's quite a challenge to install it on QGIS for Windows, which uses it's own Python interpreter.

To make it easier for the Windows end-users, we do our best to embed the depencies within the released version of the plugin, inside the `embedded_external_libs`.

Technically, the plugin tries to:

1. import Scikit-nearn from the Python interpreter used by QGIS (system on Linux, specific on Windows)
1. adds `embedded_external_libs` to the `PYTHONPATH` and then import Scikit-Learn from it

**BUT** there are some caveats because

### Linux

> Mainly tested on Ubuntu 20.04.

- {{ qgis_version_min }} =< QGIS =< {{ qgis_version_max }}
- Python 3.8+
- dependencies listed in `requirements/embedded.txt`. On Linux, you need to install by yourself. Typically, on Ubuntu:

```bash
# using the requirements file if you have the plugin repository
python3 -m pip --no-deps -U -r requirements/embedded.txt
# or directly - refer to the file to be sure use the updated good pinned versions
python3 -m pip --no-deps -U "joblib==1.1.*" "scikit-learn==1.0.*" "threadpoolctl>=2,<3"
```

:::{important}
**Remember** to look at the `requirements/embedded.txt` file to make sure you are using the right versions. The above command is just an example, a pattern.
:::

### Windows

> Mainly tested on Windows 10.0.19044.

- {{ qgis_version_min }} =< QGIS =< {{ qgis_version_max }}
- Python 3.9 (strictly)

### Use it with a different Python version (manual install)

1. Launch the `OSGeo4W Shell`. Look for it in your Windows Search or look for your QGIS install folder:
    - installed with the _all inclusive_ standalone `.msi`: `C:\Program Files\QGIS`
    - installed with the OSGeo4W with default settings: `C:\OSGeo4W`
1. Run:

  ```cmd
  python-qgis-ltr -m pip install -U pip
  python-qgis-ltr -m pip install -U setuptools wheel
  python-qgis-ltr -m pip install -U "joblib==1.1.*" "scikit-learn==1.0.*" "threadpoolctl>=2,<3"
  ```

:::{important}
**Remember** to look at the `requirements/embedded.txt` file to make sure you are using the right versions. The above command is just an example, a pattern.
:::

---

## Stable version (recomended)

This plugin is published on the official QGIS plugins repository: <https://plugins.qgis.org/plugins/RoofClassify/>.

Go to `Plugins` -> `Manage and Install Plugins`, look for the plugin and install it.

## Beta versions released

Enable experimental extensions in the QGIS plugins manager settings panel.
