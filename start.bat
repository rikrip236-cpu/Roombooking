@echo off
setlocal enabledelayedexpansion
title RoomBooking - Demarrage
cd /d "%~dp0"

echo ============================================
echo   RoomBooking - Demarrage de l'application
echo ============================================
echo.

REM --- 1. Verifier que Python est installe ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERREUR] Python n'est pas trouve dans le PATH.
    echo Installez Python 3.11+ et cochez "Add Python to PATH" pendant l'installation.
    pause
    exit /b 1
)

REM --- 2. Creer l'environnement virtuel s'il n'existe pas ---
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creation de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        echo [ERREUR] Impossible de creer l'environnement virtuel.
        pause
        exit /b 1
    )
)

REM --- 3. Activer l'environnement virtuel ---
call venv\Scripts\activate.bat

REM --- 4. Installer/mettre a jour les dependances ---
echo [INFO] Verification des dependances...
pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation des dependances.
    pause
    exit /b 1
)

REM --- 5. Verifier/creer le fichier .env (force la config MySQL/Laragon) ---
if not exist ".env" (
    if exist ".env.laragon" (
        echo [INFO] Copie de .env.laragon vers .env ...
        copy /y ".env.laragon" ".env" >nul
    ) else (
        echo [ERREUR] Aucun fichier .env trouve. Copiez .env.laragon en .env manuellement.
        pause
        exit /b 1
    )
) else (
    findstr /C:"DB_ENGINE=mysql" ".env" >nul 2>nul
    if errorlevel 1 (
        echo [ATTENTION] Le fichier .env actuel n'est pas configure pour MySQL/Laragon.
        echo ^(DB_ENGINE absent ou different de "mysql" - il pointe peut-etre vers PostgreSQL^).
        choice /c ON /m "Remplacer .env par la config Laragon/MySQL ^(O^) ou garder tel quel ^(N^)"
        if not errorlevel 2 (
            copy /y ".env" ".env.backup" >nul
            echo [INFO] Ancien .env sauvegarde en .env.backup
            copy /y ".env.laragon" ".env" >nul
            echo [INFO] .env remplace par la configuration MySQL/Laragon.
        )
    )
)

REM --- 6. Verifier que Laragon (MySQL) est demarre ---
echo [INFO] Verification de la connexion MySQL (localhost:3306)...
powershell -Command "try { $c = New-Object System.Net.Sockets.TcpClient('localhost', 3306); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>nul
if errorlevel 1 (
    echo [ATTENTION] MySQL ne repond pas sur le port 3306.
    echo Demarrez Laragon ^(bouton "Start All"^) avant de continuer.
    echo.
    choice /c ON /m "Appuyez sur O pour reessayer, N pour continuer quand meme"
    if errorlevel 2 (
        echo [INFO] Poursuite sans verification...
    ) else (
        start "" "C:\laragon\laragon.exe"
        echo Patientez que Laragon demarre puis relancez ce script.
        pause
        exit /b 1
    )
)

REM --- 7. Creer la base de donnees automatiquement (si Laragon/MySQL tourne) ---
echo [INFO] Creation automatique de la base "roombooking" si necessaire...
chcp 65001 >nul
where mysql >nul 2>nul
if errorlevel 1 (
    echo [ATTENTION] Client "mysql" introuvable dans le PATH.
    echo Ajoutez C:\laragon\bin\mysql\mysql-x.x\bin au PATH, ou creez la base
    echo "roombooking" manuellement dans HeidiSQL / phpMyAdmin.
) else (
    mysql --default-character-set=utf8mb4 -u root -e "CREATE DATABASE IF NOT EXISTS roombooking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
    if errorlevel 1 (
        echo [ATTENTION] Impossible de creer automatiquement la base. Verifiez que Laragon est demarre.
    ) else (
        echo [INFO] Base "roombooking" prete.
    )
)

REM --- 8. Creer/mettre a jour les migrations puis creer les tables ---
echo [INFO] Generation des migrations si necessaire...
python manage.py makemigrations accounts rooms bookings --noinput
echo [INFO] Creation des tables ^(migrations Django^)...
python manage.py migrate --noinput
if errorlevel 1 (
    echo [ERREUR] Echec des migrations. Verifiez la connexion a la base de donnees.
    pause
    exit /b 1
)

REM --- 9. Charger les donnees de demo (une seule fois) ---
if not exist ".demo_loaded" (
    echo [INFO] Chargement des donnees de demonstration...
    python manage.py loaddata fixtures\demo.json
    echo. > .demo_loaded
)

REM --- 10. Creer un superutilisateur si aucun n'existe ---
python check_superuser.py >nul 2>nul
if errorlevel 1 (
    echo.
    echo [INFO] Aucun compte administrateur trouve.
    echo Creation d'un super-utilisateur ^(ou Ctrl+C pour passer cette etape^) :
    python manage.py createsuperuser
)

REM --- 11. Lancer le serveur et ouvrir le navigateur ---
echo.
echo ============================================
echo   Serveur lance sur http://127.0.0.1:8000/
echo   Admin : http://127.0.0.1:8000/admin/
echo   Ctrl+C pour arreter le serveur
echo ============================================
echo.
start "" http://127.0.0.1:8000/
python manage.py runserver 0.0.0.0:8000

pause
