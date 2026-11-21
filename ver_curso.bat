@echo off
chcp 65001 >nul
REM Abre la vista previa del curso en el navegador (Ctrl+C en esta ventana para pararla)
cd /d "%~dp0"

where quarto >nul 2>nul
if %errorlevel%==0 (
  quarto preview
  goto :fin
)

REM Si Quarto no esta instalado aparte, intenta usar el que trae Positron
set "Q=%LOCALAPPDATA%\Programs\Positron\resources\app\quarto\bin\quarto.exe"
if not exist "%Q%" set "Q=%ProgramFiles%\Positron\resources\app\quarto\bin\quarto.exe"
if exist "%Q%" (
  "%Q%" preview
  goto :fin
)

echo No encuentro Quarto. Instalalo desde https://quarto.org/docs/get-started/ y vuelve a probar.
pause

:fin
