@echo off
chcp 65001 > nul
echo ==============================================================
echo        COMPILADOR DE EJECUTABLE SMARTBREAK (PYINSTALLER)
echo ==============================================================
echo.

cd /d "%~dp0\.."

echo [1/3] Verificando dependencias instaladas...
python -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org --quiet

echo [2/3] Generando assets de alta resolución...
python assets/generate_assets.py

echo [3/3] Compilando ejecutable con PyInstaller (Modo Onedir Sin Consola)...
pyinstaller --clean -y packaging/smartbreak.spec

echo.
if exist "dist\SmartBreak\SmartBreak.exe" (
    echo ==============================================================
    echo [EXITO] Compilacion completada con exito!
    echo Ubicacion del ejecutable: dist\SmartBreak\SmartBreak.exe
    echo ==============================================================
) else (
    echo ==============================================================
    echo [ERROR] No se pudo generar el ejecutable. Revisa los logs.
    echo ==============================================================
)
pause
