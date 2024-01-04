@echo off

SET QGIS_ROOT=C:\Program Files\QGIS 3.34.0
SET QT_DIR=Qt5
SET GRASS_DIR=grass83
SET PYTHON_DIR=Python39
SET PLUGINS_DIR=C:\Users\user\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\

call "%QGIS_ROOT%\bin\o4w_env.bat"

call "%QGIS_ROOT%\apps\grass\%GRASS_DIR%\etc\env.bat"


@echo off


path %PATH%;%QGIS_ROOT%\apps\qgis\bin

path %PATH%;%QGIS_ROOT%\apps\grass\%GRASS_DIR%\lib

path %PATH%;%QGIS_ROOT%\apps\%QT_DIR%\bin

path %PATH%;%QGIS_ROOT%\apps\%PYTHON_DIR%\Scripts


set PYTHONPATH=%PYTHONPATH%;%QGIS_ROOT%\apps\qgis\python;%PLUGINS_DIR%

set PYTHONHOME=%QGIS_ROOT%\apps\%PYTHON_DIR%

python "C:\Users\user\Python Scripts\Personal Projects\Run External Plugins pyqgis\qgis_main.py"
pause
