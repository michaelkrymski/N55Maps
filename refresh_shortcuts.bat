@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0refresh_shortcuts.ps1" %*
