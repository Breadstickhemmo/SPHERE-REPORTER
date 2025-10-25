# SFERA Report Generator

Система автоматизированного анализа эффективности команд разработки, интегрированная с платформой Т1 Сфера.Код.

## Обзор Функциональности

* Аутентификация пользователей
* Анализ Git-активности команд:
  * Частота и размер коммитов
  * Статистика работы с ветками
  * Анализ изменений кода
  * Временные паттерны активности
* Расчет KPI эффективности команд
* Интерактивный веб-дашборд
* Система рекомендаций для улучшения эффективности

## Технологический стек

* **Фронтенд:** React, TypeScript, CSS
* **Бэкенд:** Flask (Python)
* **База данных:** PostgreSQL с SQLAlchemy ORM
* **Миграции БД:** Flask-Migrate
* **Аутентификация:** Flask-JWT-Extended (JWT токены)
* **API Интеграция:** Requests (для Сфера.Код API)

## Структура проекта

```
/
├── README.md                # Документация проекта
├── requirements.txt         # Зависимости Python для сервера
├── .gitignore              # Файлы и папки, игнорируемые Git
├── LICENSE                 # Лицензия проекта
├── client/                 # Фронтенд-приложение (React + TypeScript)
│   ├── package.json        # Зависимости и скрипты Node.js
│   ├── tsconfig.json       # Конфигурация TypeScript
│   ├── public/             # Статические файлы
│   └── src/               # Исходный код фронтенда
│       ├── App.tsx        # Главный компонент
│       ├── types.ts       # TypeScript типы
│       ├── index.css      # Оформление
│       ├── index.tsx      # Обращение по id
│       ├── logo.svg       # logo
│       ├── assets/        # Ассеты
│       ├── styles/        # Стили
│       ├── types/         # Расширения
│       ├── utils/         # Вспомогательная функция
│       └── components/    # React-компоненты
├── server/                # Бэкенд-приложение (Flask)
│   ├── app.py            # Точка входа приложения
│   ├── config.py         # Конфигурация
│   ├── models.py         # Модели базы данных
│   ├── routes.py         # API маршруты
│   ├── auth_routes.py    # Аутентификация
│   ├── utils.py          # Вспомогательные функции
│   ├── data_collector.py   # Получение данных по коммитам
│   ├── kpi_calculator.py   # Расчёт KPI
│   ├── llm_analyzer.py     # Расчёт LLM-оценки коммита
│   ├── metrics_routes.py   # Вспомогательные функции
│   ├── sfera_api.py        # Интеграция API Sfera
│   ├── sfera_routes.py     # API Sfera маршруты
│   └── migrations/       # Миграции базы данных
```

## Установка

### Предварительные требования

* Python 3.8+
* Node.js 14+
* PostgreSQL 13+

### Настройка окружения

1. **Создание виртуального окружения Python:**

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/MacOS
source .venv/bin/activate
```

2. **Установка зависимостей:**

```bash
# Бэкенд
cd server
pip install -r requirements.txt

# Фронтенд
cd ../client
npm install
```

3. **Настройка проекта:**

Создайте файл `.env` в папке `server/`.

```bash
# Учетные данные для API Сфера.Код
SFERA_USERNAME=ВАШ_ЛОГИН_СФЕРЫ
SFERA_PASSWORD=ВАШ_ПАРОЛЬ_СФЕРЫ

# (замените на ваши данные)
DATABASE_URL=postgresql://hackathon_user:hackathon_pass@localhost:5432/hackathon_db
GIGACHAT_CREDENTIALS=ваш токен
JWT_SECRET_KEY=сгенерируйте_свой_ключ_здесь
FLASK_SECRET_KEY=сгенерируйте_другой_ключ_здесь
DEBUG=True
```

4. **Инициализация базы данных:**

Запустите `psql` (интерфейс командной строки PostgreSQL) или используйте `pgAdmin`.

Выполните следующие SQL-команды:
(Замените hackathon_user и hackathon_pass на те же значения, что и в DATABASE_URL.)

```bash
-- Создаем нового пользователя (роль)
CREATE USER hackathon_user WITH PASSWORD 'hackathon_pass';

-- Создаем новую базу данных и назначаем владельцем нашего пользователя
CREATE DATABASE hackathon_db OWNER hackathon_user;

-- Даем пользователю все права на его базу данных (важно для Flask-Migrate)
GRANT ALL PRIVILEGES ON DATABASE hackathon_db TO hackathon_user;
```

После настройки .env и создания БД, необходимо создать таблицы. Выполните команды в папке server/ с активированным .venv:

```bash
cd server
flask db init
flask db migrate -m "Initial project models"
flask db upgrade
```

## Запуск приложения

1. **Запуск бэкенда:**

```bash
cd server
flask run
```

2. **Запуск фронтенда:**

```bash
cd client
npm start
```

Приложение будет доступно по адресу http://localhost:3000