# BotBooking Demo

Telegram-бот для демонстрации записи клиентов на услугу. Клиент выбирает услугу, дату и время, вводит имя и телефон, подтверждает заявку. Администратор получает уведомление, а заявки сохраняются в SQLite через SQLAlchemy.

## Структура

```text
botbooking/
  app.py                 # сборка и запуск aiogram-приложения
  config.py              # .env и настройки
  constants.py           # услуги, даты, время
  keyboards.py           # inline-клавиатуры
  states.py              # FSM-состояния
  db/
    database.py          # engine/session/init_db
    models.py            # SQLAlchemy ORM-модели
    repository.py        # операции с заявками
  handlers/
    booking.py           # сценарий записи клиента
    admin.py             # команда /requests
  services/
    formatters.py        # форматирование сообщений
    validation.py        # проверка дат, времени и телефона
```

## Запуск через uv

1. Создайте `.env` по примеру:

```bash
copy .env.example .env
```

2. Заполните переменные:

```env
BOT_TOKEN=токен_бота_от_BotFather
ADMIN_ID=ваш_telegram_id
DATABASE_URL=sqlite:///botbooking.sqlite3
BOOKING_TIMEZONE=Europe/Moscow
```

3. Установите зависимости и запустите бота:

```bash
uv sync
uv run botbooking
```

Альтернативно:

```bash
uv run python -m botbooking
```

## Команды

- `/start` — начать запись или сбросить текущую форму. Запись доступна в личном чате.
- `/cancel` — отменить заполнение на любом шаге.
- `/requests` — показать последние 5 заявок только пользователю `ADMIN_ID` в личном чате с ботом. Команда работает и во время заполнения формы, не меняя её.