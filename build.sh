#!/bin/bash

# pyinstallerのビルド
pyinstaller *.py --onefile --clean --noconsole --additional-hooks-dir=./hooks/

