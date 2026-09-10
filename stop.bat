@echo off
title RoomBooking - Arret
echo Recherche du serveur Django sur le port 8000...

for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Arret du processus %%p ...
    taskkill /PID %%p /F >nul 2>nul
)

echo Termine.
pause
