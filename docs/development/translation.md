# Manage translations

## Requirements

Qt Linguist tools are used to manage translations. Typically on Ubuntu 22.04:

```bash
sudo apt install qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools qttools5-dev-tools
```

## Workflow

1. Update `.ts` files:

    ```bash
    pylupdate5 -noobsolete -verbose RoofClassify/resources/i18n/plugin_translation.pro
    ```

2. Translate your text using QLinguist or directly into `.ts` files.
3. Compile it:

    ```bash
    lrelease RoofClassify/resources/i18n/*.ts
    ```
