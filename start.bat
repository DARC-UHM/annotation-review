@echo off
waitress-serve --threads=3 --call application:create_app
