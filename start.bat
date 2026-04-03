@echo off
git pull
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"
python -m waitress --threads=3 --port=8000 --call application:create_app
