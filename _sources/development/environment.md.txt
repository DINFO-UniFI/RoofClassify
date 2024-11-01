# Development environment setup

Clone the repository, then follow these steps.

It's strongly recomended to develop into a virtual environment:

```bash
python3 -m venv --system-site-packages .venv
```

```{note}
We link to system packages to keep the link with installed QGIS Python libraries: PyQGIS, PyQT, etc.
```

In your virtual environment:

```bash
# use the latest pip version
python -m pip install -U pip
# install development tools
python -m pip install -U -r requirements/development.txt
# install external dependencies
python -m pip install --no-deps -U -r requirements/embedded.txt -t RoofClassify/embedded_external_libs
# install pre-commit to respect common development guidelines
pre-commit install
```

## Additionnal external dependencies

This plugin has external dependencies listed in this specific file: <requirements/embedded.txt>

Because it's still hard to install Python 3rd party packages from an index (for example <https://pypi.org>), especially on Windows or Mac systems (or even on Linux if we want to do it properly in a virtual environment), those required packages are stored in the `embedded_external_libs` folder.
