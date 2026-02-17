# 📊 Attendance Bot — Telegram бот для отметки посещаемости

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg">
  <img src="https://img.shields.io/badge/aiogram-3.x-blue">
  <img src="https://img.shields.io/badge/license-MIT-green">
  <img src="https://img.shields.io/badge/google%20sheets-API-brightgreen">
</p>

<p align="center">
  Бот для автоматизации отметки посещаемости в Telegram группах с интеграцией Google Sheets. Админ запускает сессию в личных сообщениях, бот отправляет в группу сообщение с кнопкой, студенты отмечаются, а результаты сохраняются в Google Таблицу.
</p>

---

## ✨ Возможности

| | Функция | Описание |
|---|---------|----------|
| ✅ | **Удобное управление** | Админ управляет ботом через личные сообщения, группа не засоряется командами |
| ✅ | **Чистота в группе** | Сообщение с кнопкой автоматически удаляется после завершения отметки |
| ✅ | **Без звука** | Все сообщения отправляются с отключенными уведомлениями |
| ✅ | **Автоопределение занятия** | Бот сам определяет номер следующего занятия на основе таблицы |
| ✅ | **Поддержка студентов без username** | Им автоматически ставится минус, они не могут отметиться |
| ✅ | **Детальная статистика** | Админ получает полный отчёт в личные сообщения |
| ✅ | **Google Sheets интеграция** | Все данные сохраняются в таблицу, история посещаемости не теряется |

---

## 🛠 Технологии

<div align="center">

| Технология | Назначение |
|------------|------------|
| ![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python) | Основной язык программирования |
| ![aiogram](https://img.shields.io/badge/aiogram-3.x-2C8EBB?logo=telegram) | Асинхронный фреймворк для Telegram Bot API |
| ![Google Sheets](https://img.shields.io/badge/Google%20Sheets-API-34A853?logo=google-sheets) | Хранение данных о студентах и посещаемости |
| ![gspread](https://img.shields.io/badge/gspread--asyncio-2.0.0-green) | Асинхронная работа с Google Sheets |

</div>

---

## 📋 Структура таблицы Google Sheets

<table align="center">
  <tr>
    <th>A</th>
    <th>B</th>
    <th>C</th>
    <th>D</th>
    <th>E</th>
    <th>F</th>
  </tr>
  <tr>
    <td><b>ФИО</b></td>
    <td><b>Группа</b></td>
    <td><b>tg username</b></td>
    <td><b>1 занятие</b></td>
    <td><b>2 занятие</b></td>
    <td><b>3 занятие</b></td>
  </tr>
  <tr>
    <td>Иванов И.И.</td>
    <td>101</td>
    <td>ivanov</td>
    <td>+</td>
    <td>-</td>
    <td></td>
  </tr>
  <tr>
    <td>Петров П.П.</td>
    <td>102</td>
    <td>petrov</td>
    <td>-</td>
    <td>+</td>
    <td></td>
  </tr>
  <tr>
    <td>Сидоров С.С.</td>
    <td>101</td>
    <td></td>
    <td>-</td>
    <td>-</td>
    <td></td>
  </tr>
</table>

> **Важно:**
> - Столбец C (`tg username`) — username **без символа @**
> - Если у студента нет username, ячейка остаётся пустой — такой студент **автоматически получает `-`**
> - Названия занятий начинаются с колонки D

---

## 🚀 Установка и запуск

## 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/attendance-bot.git
cd attendance-bot
```

## 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

## 3. Настройка переменных окружения

Создайте файл `.env` в корневой папке:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=1a2B3cDeFgHiJkLmNoPqRsTuVwXyZ
ADMIN_IDS=123456789,987654321
GROUP_CHAT_ID=-1001234567890
```

## 4. Настройка Google Sheets API

<details>
<summary>📸 Подробная инструкция с шагами</summary>

### Шаг 1: Создание проекта в Google Cloud Console

1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/)
2. Войдите под своим Google-аккаунтом
3. В верхней части страницы нажмите на название текущего проекта (или "Select a project")
4. Нажмите кнопку **"NEW PROJECT"**
5. Введите имя проекта, например `attendance-bot`
6. Нажмите **"CREATE"**

### Шаг 2: Включение API

1. В левом меню выберите **"APIs & Services"** → **"Library"**
2. Найдите **"Google Sheets API"** и нажмите **"ENABLE"**
3. Найдите **"Google Drive API"** и нажмите **"ENABLE"**

### Шаг 3: Создание сервисного аккаунта

1. В левом меню выберите **"APIs & Services"** → **"Credentials"**
2. Нажмите **"+ CREATE CREDENTIALS"** → **"Service Account"**
3. Заполните:
   - **Service account name**: `attendance-bot-account`
   - **Service account ID**: сгенерируется автоматически
4. Нажмите **"CREATE AND CONTINUE"**
5. В поле **"Select a role"** выберите **"Basic"** → **"Editor"**
6. Нажмите **"CONTINUE"**, затем **"DONE"**

### Шаг 4: Создание ключа доступа

1. В списке сервисных аккаунтов нажмите на созданный аккаунт
2. Перейдите на вкладку **"KEYS"**
3. Нажмите **"ADD KEY"** → **"Create new key"**
4. Выберите формат **JSON**
5. Нажмите **"CREATE"** — файл автоматически скачается
6. Переименуйте скачанный файл в **`credentials.json`**
7. Поместите файл в корневую папку проекта

### Шаг 5: Предоставление доступа к таблице

1. Откройте ваш файл `credentials.json`
2. Найдите поле **`client_email`** и скопируйте весь email
3. Откройте вашу Google Таблицу
4. Нажмите кнопку **"Share"** (в правом верхнем углу)
5. Вставьте скопированный email в поле "Add people and groups"
6. Выберите роль **"Editor"**
7. Нажмите **"Share"**

### Шаг 6: Получение ID таблицы

1. Откройте вашу Google Таблицу в браузере
2. Посмотрите на URL: https://docs.google.com/spreadsheets/d/1a2B3cDeFgHiJkLmNoPqRsTuVwXyZ/edit
3. Скопируйте часть между `/d/` и `/edit` — это ID таблицы

</details>

## 5. Получение ID группы Telegram

<details>
<summary>📸 Инструкция</summary>

### Способ 1: Через бота @getidsbot

1. Откройте Telegram
2. Найдите бота **@getidsbot**
3. Добавьте бота в вашу группу
4. Бот автоматически покажет ID группы
5. Удалите бота после получения ID

### Способ 2: Через временный код

Добавьте в `handlers.py` временный обработчик:

```python
@router.message()
async def log_chat_id(message: Message):
 print(f"Chat ID: {message.chat.id}")
```

Запустите бота локально и отправьте любое сообщение в группу — в консоли появится ID.
</details>

## 6. Добавление бота в группу и настройка прав

1. Добавьте бота в группу через информацию о группе → "Добавить участников"
2. Назначьте бота **администратором** группы
3. В BotFather отключите режим приватности:
   - Напишите `/mybots`
   - Выберите вашего бота
   - Нажмите **"Bot Settings"**
   - Нажмите **"Group Privacy"**
   - Нажмите **"Turn off"**

## 7. Запуск бота

### Локальный запуск

```bash
python main.py
```
или
```bash
python3 main.py
```

### Запуск с виртуальным окружением

**Windows:**
```bash
venv\Scripts\activate
python main.py
```

**macOS/Linux:**
```bash
source venv/bin/activate
python main.py
```

## 8. Проверка работы

После запуска бота:

1. Напишите боту в личные сообщения команду `/start`
2. Бот должен ответить приветственным сообщением
3. Если вы администратор, попробуйте `/start_session` — бот отправит сообщение с кнопкой в группу

## 9. Деплой на хостинг

### Bothost.ru (рекомендуется)

1. Зарегистрируйтесь на [Bothost.ru](https://bothost.ru)
2. Создайте новый проект
3. Подключите GitHub репозиторий
4. Добавьте переменные окружения в панели управления
5. Загрузите файл `credentials.json` через раздел "Файлы"
6. Нажмите **"Развернуть"**

### Важно для хостинга

На хостинге обязательно:
- Загрузите файл `credentials.json`
- Укажите все переменные окружения
- Убедитесь, что `gspread-asyncio==2.0.0` в requirements.txt
