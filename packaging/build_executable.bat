@echo off
chcp 65001 > nul
echo ==============================================================
echo        CONSTRUCTOR OFICIAL DE PRODUCCIÓN - SMARTBREAK v1.1.0
echo ==============================================================
echo.

cd /d "%~dp0\.."

echo [1/5] Verificando dependencias instaladas...
python -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org --quiet

echo [2/5] Generando assets de alta resolución...
python assets/generate_assets.py

echo [3/5] Ejecutando suite de pruebas unitarias biomecánicas...
python -m unittest discover tests
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Las pruebas unitarias fallaron. Abortando compilación.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [4/5] Compilando ejecutable con PyInstaller (Modo Onedir Sin Consola)...
pyinstaller --clean -y packaging/smartbreak.spec
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Falló la compilación con PyInstaller.
    pause
    exit /b %ERRORLEVEL%
)

:: Asegurar presencia del modelo en carpetas de destino
if exist "models\pose_landmarker_lite.task" (
    if not exist "dist\SmartBreak\models" mkdir "dist\SmartBreak\models"
    copy /y "models\pose_landmarker_lite.task" "dist\SmartBreak\models\pose_landmarker_lite.task" > nul
    if exist "dist\SmartBreak\_internal" (
        if not exist "dist\SmartBreak\_internal\models" mkdir "dist\SmartBreak\_internal\models"
        copy /y "models\pose_landmarker_lite.task" "dist\SmartBreak\_internal\models\pose_landmarker_lite.task" > nul
    )
)

echo.
echo [5/5] Buscando compilador Inno Setup para instalador wizard...
set "ISCC_PATH="
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC_PATH if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC_PATH if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC_PATH if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC_PATH (
    for /f "delims=" %%i in ('where iscc 2^>nul') do set "ISCC_PATH=%%i"
)

if defined ISCC_PATH (
    echo Encontrado Inno Setup en: "%ISCC_PATH%"
    echo Generando paquete instalador autoejecutable...
    "%ISCC_PATH%" packaging\SmartBreak_Installer_Nuevo.iss
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Instalador wizard creado exitosamente.
    ) else (
        echo [ADVERTENCIA] No se pudo generar el instalador wizard. El ejecutable portable sigue disponible.
    )
) else (
    echo [INFO] Inno Setup no detectado. Para generar el instalador wizard (.exe de setup), instala Inno Setup 6.
)

echo.
echo ==============================================================
if exist "dist\SmartBreak\SmartBreak.exe" (
    echo [EXITO] Compilación de SmartBreak completada!
    echo.
    echo   1. Ejecutable portable:
    echo      dist\SmartBreak\SmartBreak.exe
    if exist "dist\SmartBreak_Instalador_v1.1.exe" (
        echo.
        echo   2. Instalador de Windows con asistente:
        echo      dist\SmartBreak_Instalador_v1.1.exe
    )
    echo ==============================================================
) else (
    echo [ERROR] No se encontró dist\SmartBreak\SmartBreak.exe. Revisa los mensajes anteriores.
    echo ==============================================================
)
pause
