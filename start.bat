@echo off
git pull
waitress-serve --threads=3 --call application:create_app
