# Packaging and deployment

## Packaging

This plugin is using the [qgis-plugin-ci](https://github.com/opengisch/qgis-plugin-ci/) tool to perform packaging operations.

```bash
python -m pip install -U -r requirements/packaging.txt
```

Then use it:

```bash
# package a specific version
qgis-plugin-ci package 1.5.2
# package the latest version documented into the changelog
qgis-plugin-ci package latest
```

## Release a version

Follow the git workflow:

1. Fillfull the `CHANGELOG.md`
2. Apply a git tag with the relevant version: `git tag -a 0.3.0 {git commit hash} -m "New plugin UI"`
3. Push tag to master
4. Once the [release workflow](https://github.com/DINFO-UniFI/RoofClassify/actions/workflows/packager.yml) is over, check everything went fine
5. Double-check if the uploaded plugin on the official QGIS plugins repository is the same  as the one published on Github Release and has a relevant size. If not, fix it by manually uploading the plugin to the official QGIS plugins repository.
