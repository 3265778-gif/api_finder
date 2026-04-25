# 🚀 API Finder — Веб-приложение

## Описание

**API Finder** — веб-сервис для поиска поставщиков фармацевтических субстанций и сырья для БАДов.

### Основные возможности:
- ✅ Два режима: **Фарма (АФИ)** и **БАД (сырьё)**
- ✅ Проверка сертификатов (CEP, GMP, ISO 22000, FSSC 22000)
- ✅ Поиск поставщиков через Claude AI
- ✅ Генерация форматированных Excel-отчётов
- ✅ История всех поисков
- ✅ Доступно с любого устройства в браузере
- ✅ Работает на Windows, Linux, macOS

---

## 🛠️ Установка

### Требования:
- Python 3.10 или выше
- pip (встроен в Python)
- ANTHROPIC_API_KEY (для поиска через Claude)

### Шаг 1: Клонируйте репозиторий или скопируйте папку

```bash
cd /path/to/api_bot
```

### Шаг 2: Создайте виртуальное окружение

**На macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**На Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**На Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### Шаг 3: Установите зависимости

```bash
pip install -r requirements.txt
```

### Шаг 4: Настройте переменные окружения

Отредактируйте файл `key.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

Получить ключ: https://console.anthropic.com/account/keys

---

## 🚀 Запуск локально (для тестирования)

```bash
streamlit run web_app.py
```

Откроется окно браузера: **http://localhost:8501**

### Первый тест:
1. Выберите режим **"Фарма (АФИ)"**
2. Введите: `Caffeine`
3. Нажмите **"Начать поиск"**
4. Подождите результатов (~30 сек)

---

## 📦 Развертывание на сервере

### Вариант 1: Развертывание на Linux сервере компании

#### 1.1 Подготовка сервера

```bash
# Подключитесь к серверу
ssh user@server_ip

# Перейдите в нужную папку (например, /opt или /home)
cd /opt

# Клонируйте проект (или скопируйте файлы)
git clone <repo_url> api_finder
cd api_finder

# Или просто скопируйте папку через SCP:
# На локальной машине:
scp -r /Users/andreylisitskiy/Documents/api_bot user@server_ip:/opt/
```

#### 1.2 Установка на сервере

```bash
# Создайте виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

#### 1.3 Запуск Streamlit сервера

```bash
# Базовый запуск
streamlit run web_app.py

# Или с указанием порта (если порт 8501 занят)
streamlit run web_app.py --server.port 8080

# Или на всех сетевых интерфейсах (чтобы доступно было по IP)
streamlit run web_app.py --server.address 0.0.0.0
```

#### 1.4 Сделайте сервис постоянным (опционально)

Создайте systemd сервис (Linux):

```bash
sudo nano /etc/systemd/system/api-finder.service
```

Вставьте:

```ini
[Unit]
Description=API Finder Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/api_finder
Environment="PATH=/opt/api_finder/.venv/bin"
ExecStart=/opt/api_finder/.venv/bin/streamlit run web_app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активируйте:

```bash
sudo systemctl enable api-finder
sudo systemctl start api-finder
sudo systemctl status api-finder
```

---

### Вариант 2: Развертывание через Docker (более надежно)

#### 2.1 Создайте Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Скопируйте файлы
COPY requirements.txt .
COPY api_finder.py .
COPY web_app.py .
COPY key.env .

# Установите зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Exposе порт
EXPOSE 8501

# Запуск приложения
CMD ["streamlit", "run", "web_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

#### 2.2 Создайте образ и запустите контейнер

```bash
# Создайте образ
docker build -t api-finder .

# Запустите контейнер
docker run -p 8501:8501 -v $(pwd)/reports:/app/reports -v $(pwd)/history:/app/history api-finder
```

---

### Вариант 3: Windows сервер компании

#### 3.1 Установка на Windows

```powershell
# Откройте PowerShell от администратора

# Перейдите в папку
cd "C:\Program Files\api_finder"

# Создайте виртуальное окружение
python -m venv .venv

# Активируйте
.\.venv\Scripts\Activate.ps1

# Установите зависимости
pip install -r requirements.txt
```

#### 3.2 Создайте автозагрузку (Windows Task Scheduler)

1. Откройте **Task Scheduler** (Планировщик задач)
2. **Create Basic Task** (Создать простую задачу)
3. **Name:** `API Finder`
4. **Trigger:** `At startup` (При запуске)
5. **Action:** `Start a program`
   - Program: `C:\Program Files\api_finder\.venv\Scripts\streamlit.exe`
   - Arguments: `run web_app.py --server.port 8501 --server.address 0.0.0.0`
   - Start in: `C:\Program Files\api_finder`

---

## 📍 Доступ к приложению

После развертывания на сервере:

### Локально:
```
http://localhost:8501
```

### По сетевому адресу:
```
http://<IP_СЕРВЕРА>:8501
```

### Примеры:
- `http://192.168.1.100:8501` (если сервер в локальной сети)
- `http://api-finder.company.ru:8501` (если есть доменное имя)

---

## 🔒 Безопасность

1. **Убедитесь, что `key.env` содержит корректный ANTHROPIC_API_KEY**
2. **Не публикуйте API ключ в публичных репозиториях**
3. **Если нужна аутентификация**, используйте nginx с basicAuth или Streamlit authentication

---

## 📁 Структура файлов

```
api_finder/
├── api_finder.py              # Основной модуль поиска
├── web_app.py                 # Streamlit приложение 👈 ЗАПУСКАТЬ ЭТО
├── agent.py                   # LangChain агент (опционально)
├── telegram_bot.py            # Telegram интерфейс (опционально)
├── batch_search.py            # Пакетный поиск (опционально)
├── requirements.txt           # Зависимости
├── key.env                    # Переменные окружения
├── api_list.txt               # Список АФИ
│
├── .streamlit/
│   └── config.toml            # Конфиг Streamlit
│
├── reports/                   # 📁 Excel и JSON отчёты (создаются автоматически)
├── history/                   # 📁 История поисков (создаётся автоматически)
└── README.md                  # Этот файл
```

---

## 🧪 Тестирование

### Тест 1: Локальный поиск

```bash
streamlit run web_app.py
```

1. Откройте браузер: `http://localhost:8501`
2. Введите `Caffeine`
3. Нажмите "Начать поиск"
4. Проверьте, что появляются поставщики и можно скачать Excel

### Тест 2: История

1. Выполните несколько поисков
2. Откройте вкладку "История"
3. Проверьте, что все поиски сохранены

### Тест 3: Скачивание файлов

1. Выполните поиск
2. Нажмите "Скачать Excel отчёт"
3. Проверьте, что файл скачался и открывается

---

## 🛠️ Решение проблем

### Проблема: `ModuleNotFoundError: No module named 'streamlit'`

**Решение:**
```bash
pip install -r requirements.txt
```

### Проблема: `ANTHROPIC_API_KEY не найден`

**Решение:**
1. Проверьте, что файл `key.env` существует
2. Добавьте: `ANTHROPIC_API_KEY=sk-ant-xxxxxxx`
3. Перезагрузите приложение

### Проблема: Порт 8501 уже занят

**Решение:**
```bash
streamlit run web_app.py --server.port 8080
```

### Проблема: Приложение медленное

1. Проверьте интернет соединение
2. Claude API может быть перегружена — подождите
3. Используйте батчевый поиск для больших списков

---

## 📞 Поддержка

Если что-то не работает:

1. Проверьте логи: `streamlit run web_app.py` показывает ошибки в консоли
2. Убедитесь, что ANTHROPIC_API_KEY корректный
3. Проверьте интернет соединение
4. Обновите зависимости: `pip install --upgrade -r requirements.txt`

---

## 📜 Лицензия

Внутреннее ПО компании. Не распространяется.

---

## Приятного использования! 🎉

Если возникают вопросы — смотрите консоль для ошибок!
