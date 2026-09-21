@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo   RoomBooking - Correction du graphe de migrations
echo ============================================
echo.

set MIGDIR=apps\bookings\migrations

echo [1/4] Suppression du fichier de migration orphelin...
if exist "%MIGDIR%\0004_booking_day_schedules.py" (
    del /f /q "%MIGDIR%\0004_booking_day_schedules.py"
    echo     - 0004_booking_day_schedules.py supprime  [OK]
) else (
    echo     - 0004_booking_day_schedules.py deja absent  [OK]
)

echo.
echo [2/4] Nettoyage des caches Python (__pycache__ / *.pyc)...
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc >nul 2>&1
echo     - caches nettoyes  [OK]

echo.
echo [3/4] Detection de l'interpreteur Python...
if exist "venv\Scripts\python.exe" (
    set "PY=venv\Scripts\python.exe"
) else (
    set "PY=python"
)
echo     - interpreteur : !PY!

echo.
echo [4/4] Verification du graphe puis application des migrations...
echo.
echo --- Etat des migrations de l'application bookings ---
!PY! manage.py showmigrations bookings
echo.
if errorlevel 1 goto :err
echo --- Application des migrations ---
!PY! manage.py migrate
if errorlevel 1 goto :err

echo.
echo ============================================
echo   TERMINE - cherchez la ligne :
echo     "Applying bookings.0005_booking_day_schedules... OK"
echo ============================================
pause
exit /b 0

:err
echo.
echo [ERREUR] Une commande a echoue.
echo   - Verifiez que MySQL/Laragon est demarre ("Start All")
echo   - Verifiez la base "roombooking" et le fichier .env
pause
exit /b 1
