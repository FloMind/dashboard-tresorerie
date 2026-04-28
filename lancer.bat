@echo off
chcp 65001 > nul
title FloMind -- Dashboard Tresorerie

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   FloMind — Dashboard Tresorerie         ║
echo  ║   Portfolio CDG × Data × IA              ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Verifier Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python non trouve. Installer Python 3.10+ depuis python.org
    pause & exit /b 1
)

:: Creer le venv si absent
if not exist "venv\" (
    echo [1/3] Creation de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 ( echo [ERREUR] Echec creation venv & pause & exit /b 1 )
)

:: Activer et installer les dependances
echo [2/3] Installation des dependances...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

:: Detecter un port libre (8502 ou 8503)
set PORT=8502
netstat -an | find ":%PORT% " > nul 2>&1
if not errorlevel 1 (
    set PORT=8503
    netstat -an | find ":%PORT% " > nul 2>&1
    if not errorlevel 1 (
        echo [ERREUR] Ports 8502 et 8503 occupes. Fermer d'autres instances.
        pause & exit /b 1
    )
)

:: Lancer Streamlit
echo [3/3] Lancement sur http://localhost:%PORT%
echo.
echo  Appuyer sur Ctrl+C pour arreter.
echo.
streamlit run app.py --server.port %PORT%

deactivate
