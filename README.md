<div align="center">
  <h1>Personal Telegram Bot</h1>
  <h3>Telegram бот с таймерами, будильниками, упоминаниями и множеством других полезных функций.</h3>

  [![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/hadisjane/nova/releases/tag/v1.2.0)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/hadisjane/nova/blob/main/LICENSE)

  [![GitHub](https://img.shields.io/badge/GitHub-00ADD8?style=flat&logo=github&logoColor=white)](https://github.com/hadisjane/nova)
  [![Python Version](https://img.shields.io/badge/Python-3.12+-00ADD8?style=flat&logo=python)](https://www.python.org/)
  [![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?logo=telegram&logoColor=white)](https://telegram.org/)
  [![Telethon](https://img.shields.io/badge/Telethon-00ADD8?style=flat&logo=telethon&logoColor=white)](https://docs.telethon.dev/)
</div>

---

## ✨ Возможности

### ⏰ Таймеры
- `/timer 30s` - таймер с обратным отсчетом (30 секунд)
- `/timer 5m 100` - таймер + спам 100 сообщений в конце
- `/countdown 60` - простой обратный отсчет (60 секунд)

### 🔔 Будильники
- `/wake 10m` - будильник через 10 минут (10 сообщений в ЛС)
- `/wake 30m 50` - будильник с 50 сообщениями
- `/remind 5m "купить молоко"` - напоминание с текстом

### 👥 Упоминания
- `/mention @user 30` - упомянуть 30 раз
- `/mention @user 5 2s` - с интервалом 2 секунды
- `/spam "текст" 10` - спам текстом
- `/spam @user "привет" 5` - спам пользователю

### 🎭 Развлечения
- `/quote` - случайная цитата
- `/addquote "цитата"` - добавить новую цитату
- `/joke` - случайная шутка  
- `/addjoke "шутка"` - добавить новую шутку
- `/ascii "HELLO"` - ASCII арт
- `/rps камень` - камень-ножницы-бумага
- `/coin` - подбросить монетку
- `/dice 20` - бросить кубик (1-20)
- `/8ball "вопрос?"` - магический шар
- `/random 1 100` - случайное число
- `/meme` - случайный мем
- `/morning [1-3]` - утреннее сообщение (1 - общий, 2 - для друзей/кентов, 3 - для девушки/подруги)

### 🧮 Утилиты
- `/calc 2+2*5` - калькулятор
- `/hash "текст"` - MD5 хеш
- `/hash sha256 "текст"` - SHA256 хеш

### ⚙️ Управление
- `/cancel timer` - отменить все таймеры
- `/cancel timer <id>` - отменить конкретный таймер по ID
- `/cancel wake` - отменить все будильники
- `/cancel wake <id>` - отменить конкретный будильник по ID
- `/cancel mention` - отменить все упоминания
- `/cancel mention <id>` - отменить конкретное упоминание по ID
- `/cancel all` - отменить всё
- `/clear 10` - удалить 10 своих сообщений
- `/clear sender 10` - удалить 10 сообщений от бота-отправщика
- `/clear sender all` - удалить все сообщения от бота-отправщика
- `/clear user 10` - удалить 10 сообщений пользователя (ответом на сообщение)
- `/clear chat` - очистить весь чат (нужны права администратора)
- `/list all` - список активных задач
- `/ping` - проверка скорости
- `/uptime` - время работы
- `/stats` - статистика команд
- `/help` - эта справка
- `/stop` - остановка бота

## 🚀 Установка

### 1. Требования
- Python 3.9+
- Telegram аккаунт
- API ключи Telegram

### 2. Получение API ключей
1. Перейдите на https://my.telegram.org/apps
2. Создайте новое приложение
3. Сохраните `API_ID` и `API_HASH`
4. Узнайте свой User ID у бота @userinfobot

### 3. Установка зависимостей
```bash
git clone https://github.com/hadisjane/personal_bot.git
cd personal_bot
pip install -r requirements.txt
```

### 4. Настройка
1. Скопируйте `.env.example` в `.env`:
```bash
cp .env.example .env
```

2. Отредактируйте `.env` файл:
```env
API_ID=1234567
API_HASH=your_api_hash
PHONE_NUMBER=+1234567890
BOT_OWNER_ID=123456789
SENDER_BOT_API=123456789:abcdef1234567890abcdef1234567890
```

### 5. Запуск
```bash
python pbot.py
```

При первом запуске введите код подтверждения из Telegram.

## 📁 Структура проекта

```
personal_bot/
├── pbot.py                 # Основной файл запуска
├── config.py              # Конфигурация
├── requirements.txt       # Зависимости
├── .env                   # Настройки (создайте сами)
├── data/                  # Данные (создается автоматически)
│   ├── timers.json       # Активные таймеры
│   ├── wake_alarms.json  # Будильники
│   ├── mentions.json     # Упоминания
│   ├── reminders.json    # Напоминания
│   └── stats.json        # Статистика
├── handlers/              # Обработчики команд
│   ├── timer_handler.py  # Таймеры
│   ├── wake_handler.py   # Будильники
│   ├── json_storage.py   # Хранилище JSON
│   ├── timer_parser.py   # Парсинг таймеров
│   ├── mention_handler.py # Упоминания
│   ├── fun_handler.py    # Развлечения
│   └── system_handler.py # Системные команды
├── utils/                 # Утилиты
│   ├── time_parser.py    # Парсинг времени
│   ├── json_storage.py   # Хранилище JSON
│   └── message_utils.py  # Утилиты сообщений
└── assets/               # Ресурсы
    ├── quotes.json       # Цитаты
    ├── jokes.json        # Шутки
    └── ascii_art.json    # ASCII арт
```

## 🔧 Использование

### Единицы времени
- `s` - секунды (30s)
- `m` - минуты (5m)
- `h` - часы (2h)
- `d` - дни (1d)

### Примеры команд

**Простой таймер:**
```
/timer 30s
```

**Таймер со спамом:**
```
/timer 5m 50
```

**Будильник:**
```
/wake 10m
/wake 1h 20
```

**Напоминание:**
```
/remind 30m "встреча с клиентом"
/remind 2h "позвонить маме"
```

**Упоминания:**
```
/mention @username 10
/mention @username 5 3s
```

**Спам:**
```
/spam "привет!" 5
/spam @username "как дела?" 3
```

**Развлечения:**
```
/quote
/joke
/ascii "HELLO"
/rps камень
/8ball "буду ли я богатым?"
```

**Управление:**
```
/list all
/cancel timer
/stats
```

## ⚠️ Ограничения безопасности

- Максимальное время таймера: 24 часа
- Максимальное количество спама: 1000 сообщений
- Максимальное количество упоминаний: 100
- Кулдаун между командами: 0.5 секунды

## 🔒 Безопасность

- Бот работает только с вашим аккаунтом (проверка BOT_OWNER_ID)
- Все данные хранятся локально в JSON файлах
- Логирование всех действий в bot.log
- Автоматическое создание резервных копий

## 🐛 Отладка

### Логи
Все действия записываются в файл `bot.log`:
```bash
tail -f bot.log
```

### Частые проблемы

**"Неправильный аккаунт"**
- Проверьте BOT_OWNER_ID в .env файле

**"API_ID и API_HASH должны быть установлены"**
- Проверьте настройки в .env файле

**Бот не отвечает на команды**
- Убедитесь что команды отправляются от вашего аккаунта
- Проверьте логи на наличие ошибок

**Таймеры не восстанавливаются после перезапуска**
- Проверьте права на запись в папку data/
- Убедитесь что JSON файлы не повреждены

## 📝 Разработка

### Добавление новых команд

1. Создайте обработчик в соответствующем файле handlers/
2. Зарегистрируйте команду в main.py
3. Добавьте справку в system_handler.py
4. Обновите README.md

### Создание резервной копии
```python
backup_dir = await storage.create_backup()
print(f"Резервная копия создана в {backup_dir}")
```

## 📄 Лицензия

MIT License - используйте и модифицируйте как хотите!

## 🤝 Вклад в проект

1. Fork проекта
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📞 Поддержка

Если у вас возникли проблемы:

1. Проверьте логи в bot.log
2. Убедитесь что все зависимости установлены
3. Проверьте настройки в .env файле
4. Создайте Issue на GitHub

## 👨‍💻 Автор

- hadisjane

---

**Наслаждайтесь использованием вашего персонального Telegram бота! 🎉**