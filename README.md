# 🔍 API Finder — Поиск поставщиков фармацевтических субстанций

Веб-сервис для поиска производителей активных фармацевтических ингредиентов (АФИ) и сырья для БАДов с проверкой сертификатов.

## ✨ Возможности

- 🔎 **Два режима поиска**:
  - **Фарма (АФИ)** — проверка CEP (EDQM) и GMP сертификатов
  - **БАД (сырьё)** — проверка ISO 22000, FSSC 22000, GMP

- 🧪 **Поиск поставщиков** через Claude AI
- 📊 **Генерация Excel отчетов** с цветовой индикацией
- 📜 **История всех поисков** на отдельной странице
- 🌐 **Веб-интерфейс** — доступно с любого браузера
- 💾 **Сохранение результатов** в Excel и JSON

## 🚀 Быстрый старт (локально)

### Требования
- Python 3.10+
- ANTHROPIC_API_KEY (получить на https://console.anthropic.com/account/keys)

### Установка

```bash
# Клонируйте репозиторий
git clone <repository_url>
cd api_finder

# Создайте виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt

# Создайте файл key.env
echo "ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxx" > key.env

# Запустите приложение
streamlit run app.py
```

Откроется: http://localhost:8501

## 📱 Развертывание на Streamlit Cloud (онлайн)

### Шаг 1: Создайте GitHub репозиторий
1. Создайте аккаунт на [GitHub.com](https://github.com)
2. Создайте новый репозиторий
3. Загрузите туда ваши файлы (все файлы из папки api_finder)

### Шаг 2: Добавьте секреты для Streamlit Cloud
В файле `.streamlit/secrets.toml` добавьте:
```toml
ANTHROPIC_API_KEY = "sk-ant-xxxxxxxxxxxxx"
```

### Шаг 3: Разверните на Streamlit Cloud
1. Перейдите на [share.streamlit.io](https://share.streamlit.io/)
2. Нажмите "Create app"
3. Выберите:
   - GitHub репозиторий
   - Ветка: `main`
   - Main file: `app.py`
4. Нажмите "Deploy"

**Готово!** Ваше приложение будет доступно по URL вида: `https://api-finder-xxxxx.streamlit.app`

## 📁 Структура проекта

```
api_finder/
├── app.py                      # Главное Streamlit приложение
├── api_finder.py               # Основная логика поиска
├── agent.py                    # LangChain агент (опционально)
├── telegram_bot.py             # Telegram интерфейс (опционально)
├── batch_search.py             # Пакетный поиск (опционально)
├── requirements.txt            # Зависимости Python
├── key.env                     # Переменные окружения (не загружать!)
├── .gitignore                  # Файлы для игнорирования
├── .streamlit/
│   ├── config.toml            # Конфиг Streamlit
│   └── secrets.toml           # Секреты (для облака)
├── reports/                    # 📁 Excel и JSON отчеты
└── history/                    # 📁 История поисков
```

## 🔐 Безопасность

- **НИКОГДА** не загружайте `key.env` на GitHub!
- Для облака используйте `.streamlit/secrets.toml`
- Репозиторий можно сделать приватным, если код секретный

## 📊 Источники данных

- **PubChem** — химические данные (бесплатно)
- **Claude API** — поиск поставщиков (~$0.02 за запрос)
- **ChEMBL** — фармакологические данные (опционально)
- **FDA NDC** — регулятивный статус (опционально)

## 🛠️ Технический стек

- **Framework**: Streamlit 1.56+
- **Язык**: Python 3.10+
- **AI**: Claude (Anthropic API)
- **HTTP**: httpx
- **Excel**: openpyxl
- **Хранилище**: JSON файлы

## 📖 Документация

Смотрите [DEPLOYMENT_README.md](DEPLOYMENT_README.md) для подробной инструкции по развертыванию на разные сервера.

## 💡 Первый тест

1. Запустите локально: `streamlit run app.py`
2. Введите: `Caffeine`
3. Выберите режим "Фарма (АФИ)"
4. Нажмите "Начать поиск"
5. Скачайте Excel отчет
6. Проверьте историю

## ❓ Помощь

Если что-то не работает:
1. Проверьте `requirements.txt`
2. Убедитесь что ANTHROPIC_API_KEY корректный
3. Смотрите консоль для ошибок

## 📞 Связь

Внутреннее приложение компании. Вопросы и предложения приветствуются!

---

**Готово к использованию!** 🎉
