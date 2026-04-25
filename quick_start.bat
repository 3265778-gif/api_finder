@echo off
REM quick_start.bat — Быстрый старт API Finder для Windows
REM Использование: запустите этот файл двойным кликом

setlocal enabledelayedexpansion

echo.
echo ════════════════════════════════════════════════
echo   🚀 API Finder — Быстрый старт (Windows)
echo ════════════════════════════════════════════════
echo.

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.10+
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python найден: %PYTHON_VERSION%

REM Проверяем виртуальное окружение
if not exist ".venv" (
    echo 📦 Создаю виртуальное окружение...
    python -m venv .venv
)

REM Активируем окружение
echo 🔌 Активирую окружение...
call .venv\Scripts\activate.bat

REM Устанавливаем зависимости
echo 📦 Устанавливаю зависимости...
pip install -q -r requirements.txt

REM Проверяем key.env
if not exist "key.env" (
    echo.
    echo ⚠️  Файл key.env не найден!
    echo.
    echo Создайте файл key.env со следующим содержимым:
    echo.
    echo     ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
    echo.
    echo Получить ключ: https://console.anthropic.com/account/keys
    echo.
    pause
    exit /b 1
)

echo ✅ key.env найден

echo.
echo ════════════════════════════════════════════════
echo.
echo   ✅ Все готово! Запускаю приложение...
echo.
echo   🌐 Откройте браузер: http://localhost:8501
echo.
echo   Закройте это окно для остановки
echo.
echo ════════════════════════════════════════════════
echo.

streamlit run web_app.py

pause
