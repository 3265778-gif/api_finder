#!/bin/bash
# quick_start.sh — Быстрый старт API Finder
# Использование: bash quick_start.sh

set -e

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 API Finder — Быстрый старт"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python найден: $PYTHON_VERSION"

# Проверяем виртуальное окружение
if [ ! -d ".venv" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python3 -m venv .venv
fi

# Активируем окружение
echo "🔌 Активирую окружение..."
source .venv/bin/activate

# Устанавливаем зависимости
echo "📦 Устанавливаю зависимости..."
pip install -q -r requirements.txt

# Проверяем key.env
if [ ! -f "key.env" ]; then
    echo ""
    echo "⚠️  Файл key.env не найден!"
    echo ""
    echo "Создайте файл key.env со следующим содержимым:"
    echo ""
    echo "    ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx"
    echo ""
    echo "Получить ключ: https://console.anthropic.com/account/keys"
    echo ""
    exit 1
fi

# Загружаем окружение и проверяем ключ
export $(cat key.env | xargs)

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "❌ ANTHROPIC_API_KEY не установлен в key.env!"
    exit 1
fi

echo "✅ ANTHROPIC_API_KEY найден"

# Запускаем приложение
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ✅ Все готово! Запускаю приложение..."
echo ""
echo "  🌐 Откройте браузер: http://localhost:8501"
echo ""
echo "  Нажмите Ctrl+C для остановки"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

streamlit run web_app.py
