# Installation

## Requirements

The plugin's logic is mainly based on a well-known machine learning toolkit: [scikit-learn](https://scikit-learn.org/stable/). To work, the plugin needs it and it's quite a challenge to install it on QGIS for Windows, because QGIS uses its own Python interpreter and doesn't make it easy to use packages manager (`pip`).

To make it easier for Windows end-users, we did our best to embed the dependencies within the released version of the plugin, inside the `embedded_external_libs` folder.

Technically, the plugin tries to:

1. import Scikit-learn from the Python interpreter used by QGIS (system on Linux, specific on Windows)
1. add `embedded_external_libs` to the `PYTHONPATH` and then import Scikit-Learn from it

**BUT** there are some caveats because

### Linux

> Mainly tested on Ubuntu 20.04.

- {{ qgis_version_min }} =< QGIS =< {{ qgis_version_max }}
- Python 3.8+
- dependencies listed in `requirements/embedded.txt`. On Linux, you need to install them by yourself. Typically, on Ubuntu:

```bash
# using the requirements file if you have the plugin repository
python3 -m pip install --no-deps -U -r requirements/embedded.txt
# or directly - refer to the file to be sure of using the right updated pinned versions
python3 -m pip install --no-deps -U "joblib==1.1.*" "scikit-learn==1.0.*" "threadpoolctl>=2,<3"
```

:::{important}
**Remember** to look at the `requirements/embedded.txt` file to make sure you are using the right versions. The above command is just an example, a pattern.
:::

### Windows

> Mainly tested on Windows 10.0.19044.

- {{ qgis_version_min }} =< QGIS =< {{ qgis_version_max }}
- Python 3.9 (strictly)

### Use it with a different Python version (manual install)

1. Launch the `OSGeo4W Shell`. Look for it in your Windows Search or directly into your QGIS install folder:
    - installed with the _all inclusive_ standalone `.msi`: `C:\Program Files\QGIS`
    - installed with the OSGeo4W with default settings: `C:\OSGeo4W`
1. Run:

  ```batch
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

## Alternate plugins repository

During the release workflow (see [Packaging and deployment](/development/packaging.md)), the plugin is packaged and released on the official QGIS plugins repository but also as a GitHub Release, right aside the repository.

You can add the following URL to the QGIS extensions repositories, in the `Settings` tab of the `Plugins Manager` window (see [official documentation](https://docs.qgis.org/3.16/en/docs/user_manual/plugins/plugins.html#the-settings-tab)):

```html
https://github.com/DINFO-UniFI/RoofClassify/releases/latest/download/plugins.xml
```

:::{warning}
As GitHub Releases publishes only stable releases through its *latest* API, only not tagged releases as pre-release are available.
:::
