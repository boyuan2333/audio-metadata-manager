@echo off
setlocal

pushd "%~dp0\.." >nul

if not defined AMM_LIBRARY set "AMM_LIBRARY=.\out\library.json"
if not defined AMM_SAMPLES set "AMM_SAMPLES=.\audio"
if not defined AMM_PORT set "AMM_PORT=8000"

if not exist "%AMM_LIBRARY%" (
    echo AMM library file was not found:
    echo   %AMM_LIBRARY%
    echo.
    echo Create one first, for example:
    echo   python app.py index --input .\audio --output .\out\library.json --recursive
    echo.
    echo Or set AMM_LIBRARY to an existing library JSON path before running this script.
    popd >nul
    exit /b 1
)

echo Starting AMM Web UI...
echo   Library: %AMM_LIBRARY%
echo   Samples: %AMM_SAMPLES%
echo   Port: %AMM_PORT%
echo.

python web_server.py --library "%AMM_LIBRARY%" --samples "%AMM_SAMPLES%" --port "%AMM_PORT%"
set "AMM_EXIT_CODE=%ERRORLEVEL%"

popd >nul
exit /b %AMM_EXIT_CODE%
