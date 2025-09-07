@echo off
setlocal
REM Optional: prefer venv if present
set "PY=python"
if exist "%~dp0..\..\..\..\orchestrator\servers\obsidian-mcp-python\.venv\Scripts\python.exe" set "PY=%~dp0..\..\..\..\orchestrator\servers\obsidian-mcp-python\.venv\Scripts\python.exe"

REM Preserve Windows essentials; Codex clears env, so be explicit
set "APPDATA=%APPDATA%"
set "LOCALAPPDATA=%LOCALAPPDATA%"
set "HOME=%USERPROFILE%"
set "SystemRoot=%SystemRoot%"
set "COMSPEC=%COMSPEC%"
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=C:\Users\ali95\Documents\Dev\orchestrator\servers\obsidian-mcp-python"
REM set "OBSIDIAN_API_KEY=YOUR_KEY"  REM (prefer .env; only use here if needed)

pushd "C:\Users\ali95\Documents\Dev\orchestrator\servers\obsidian-mcp-python"
"%PY%" -u main.py 1>> "%USERPROFILE%\.codex\obsidian-mcp.out.log" 2>> "%USERPROFILE%\.codex\obsidian-mcp.err.log"
set "EC=%ERRORLEVEL%"
popd
exit /b %EC%
