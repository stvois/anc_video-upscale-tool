@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "APP=%~dp0video_upscaler_gui.py"
set "CHECK_ONLY=0"
if /I "%~1"=="--check" set "CHECK_ONLY=1"

rem Prefer standalone and per-user Python 3.10+ installations. This avoids a
rem broken or old py/pyw launcher taking precedence on another computer.
call :try_runtime "%SystemDrive%\Python314"
if defined LAUNCHED goto done
call :try_runtime "%SystemDrive%\Python313"
if defined LAUNCHED goto done
call :try_runtime "%SystemDrive%\Python312"
if defined LAUNCHED goto done
call :try_runtime "%SystemDrive%\Python311"
if defined LAUNCHED goto done
call :try_runtime "%SystemDrive%\Python310"
if defined LAUNCHED goto done
call :try_runtime "%LocalAppData%\Programs\Python\Python314"
if defined LAUNCHED goto done
call :try_runtime "%LocalAppData%\Programs\Python\Python313"
if defined LAUNCHED goto done
call :try_runtime "%LocalAppData%\Programs\Python\Python312"
if defined LAUNCHED goto done
call :try_runtime "%LocalAppData%\Programs\Python\Python311"
if defined LAUNCHED goto done
call :try_runtime "%LocalAppData%\Programs\Python\Python310"
if defined LAUNCHED goto done

where py >nul 2>nul
if errorlevel 1 goto missing_python
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 goto missing_python
if "%CHECK_ONLY%"=="1" (
    py -3 -c "import sys; print('Compatible Python:', sys.executable, sys.version.split()[0])"
    goto done
)
where pyw >nul 2>nul
if errorlevel 1 goto py_console
start "" pyw -3 "%APP%"
goto done

:py_console
py -3 "%APP%"
if errorlevel 1 pause
goto done

:try_runtime
set "RUNTIME=%~1"
if not exist "%RUNTIME%\python.exe" exit /b 0
"%RUNTIME%\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 exit /b 0
if "%CHECK_ONLY%"=="1" goto report_runtime
if not exist "%RUNTIME%\pythonw.exe" goto start_console_runtime
start "" "%RUNTIME%\pythonw.exe" "%APP%"
set "LAUNCHED=1"
exit /b 0

:start_console_runtime
start "" "%RUNTIME%\python.exe" "%APP%"
set "LAUNCHED=1"
exit /b 0

:report_runtime
"%RUNTIME%\python.exe" -c "import sys; print('Compatible Python:', sys.executable, sys.version.split()[0])"
set "LAUNCHED=1"
exit /b 0

:missing_python
echo.
echo Compatible Python was not found.
echo Install Python 3.10 or later with the Python Launcher option enabled.
echo The program does not support Python 3.6.
pause
exit /b 1

:done
endlocal
exit /b 0
