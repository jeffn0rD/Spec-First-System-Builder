@echo off
REM FastAPI Backend Setup Script for Windows 11
REM ============================================

echo.
echo ========================================
echo FastAPI Backend Setup
echo ========================================
echo.

REM Step 1: Create Project Directory and Virtual Environment
echo Step 1: Creating Project Directory and Virtual Environment...
echo --------------------------------------------------------

REM Create project directory
if not exist fastapi-backend (
    mkdir fastapi-backend
    echo Created fastapi-backend directory
) else (
    echo fastapi-backend directory already exists
)

cd fastapi-backend

REM Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Virtual environment activated (you should see (venv) in your prompt)
echo.

REM Step 2: Create Project Structure
echo Step 2: Creating Project Structure...
echo --------------------------------

REM Create directory structure
if not exist app mkdir app
if not exist app\api mkdir app\api
if not exist app\core mkdir app\core
if not exist app\models mkdir app\models
if not exist app\services mkdir app\services
if not exist tests mkdir tests

New-Item -ItemType File -Path "app\__init__.py"
New-Item -ItemType File -Path "app\api\__init__.py"
New-Item -ItemType File -Path "app\core\__init__.py"
New-Item -ItemType File -Path "app\models\__init__.py"
New-Item -ItemType File -Path "app\services\__init__.py"
New-Item -ItemType File -Path "tests\__init__.py"

echo.
echo Project structure created:
echo   - app\
echo   - app\api\
echo   - app\core\
echo   - app\models\
echo   - app\services\
echo   - tests\
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Install FastAPI: pip install fastapi uvicorn
echo 2. Start developing your application
echo.

New-Item -ItemType File -Path "requirements.txt"

rem COPY THE REQUIREMENTS.TXT 

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list

rem COPY app/core/config.py


rem New-Item -ItemType File -Path ".env"
rem COPY .env


REM Keep the command prompt open in the virtual environment
cmd /k
