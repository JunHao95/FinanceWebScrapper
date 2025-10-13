@echo off
REM Startup script for Stock Financial Metrics Scraper Web Application (Windows)

echo ==================================================
echo Stock Financial Metrics Scraper - Web Application
echo ==================================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo Dependencies installed
)

REM Check for .env file
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo    Email functionality will not work without proper configuration.
    echo    Please create a .env file with your email settings.
    echo    See WEBAPP_README.md for details.
    echo.
)

REM Check for config.json
if not exist "config.json" (
    echo.
    echo WARNING: config.json not found!
    echo    Copying from config.json.example...
    if exist "config.json.example" (
        copy config.json.example config.json
        echo config.json created from example
    )
    echo.
)

REM Get port from environment or use default
if "%PORT%"=="" set PORT=5173

echo.
echo ==================================================
echo Starting web application on port %PORT%...
echo ==================================================
echo.
echo Access the application at:
echo    http://localhost:%PORT%
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the Flask application
python webapp.py

pause
