#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import Message

# Load environment variables from .env file
load_dotenv()

from config import config
from handlers.timer_handler import TimerHandler
from handlers.wake_handler import WakeHandler
from handlers.mention_handler import MentionHandler
from handlers.fun_handler import FunHandler
from handlers.system_handler import SystemHandler
from handlers.interactions import InteractionsHandler
from utils.json_storage import JsonStorage
from utils.time_parser import TimeParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PersonalBot:
    def __init__(self):
        self.config = config
        self.storage = JsonStorage()
        self.time_parser = TimeParser()
        self.start_time = datetime.now()

        # Инициализация клиентов (без запуска)
        self.client = TelegramClient(
            'bot_session',
            int(os.getenv('API_ID')),
            os.getenv('API_HASH')
        )
        self.sender_client = None
        sender_bot_token = os.getenv('SENDER_BOT_API')
        if sender_bot_token:
            # Используем разные ID сессий, чтобы избежать конфликтов
            self.sender_client = TelegramClient(
                'sender_bot_session',
                int(os.getenv('API_ID')), # Можно использовать те же API ID/HASH
                os.getenv('API_HASH')
            )

    def setup_handlers(self):
        """Регистрация всех обработчиков команд"""
        
        # Таймеры
        @self.client.on(events.NewMessage(pattern=r'^/timer\s+(.+)', outgoing=True))
        async def timer_command(event):
            await self.timer_handler.handle_timer(event)

        @self.client.on(events.NewMessage(pattern=r'^/countdown\s+(\d+)', outgoing=True))
        async def countdown_command(event):
            await self.timer_handler.handle_countdown(event)

        # Будильники и напоминания
        @self.client.on(events.NewMessage(pattern=r'^/wake\s+(.+)', outgoing=True))
        async def wake_command(event):
            await self.wake_handler.handle_wake(event)

        @self.client.on(events.NewMessage(pattern=r'^/remind\s+(.+)', outgoing=True))
        async def remind_command(event):
            await self.wake_handler.handle_remind(event)

        # Упоминания и спам
        @self.client.on(events.NewMessage(pattern=r'^/mention\s+(.+)', outgoing=True))
        async def mention_command(event):
            await self.mention_handler.handle_mention(event)

        @self.client.on(events.NewMessage(pattern=r'^/spam\s+(.+)', outgoing=True))
        async def spam_command(event):
            await self.mention_handler.handle_spam(event)

        # Развлекательные команды
        @self.client.on(events.NewMessage(pattern=r'^/quote$', outgoing=True))
        async def quote_command(event):
            await self.fun_handler.handle_quote(event)

        @self.client.on(events.NewMessage(pattern=r'^/joke$', outgoing=True))
        async def joke_command(event):
            await self.fun_handler.handle_joke(event)

        @self.client.on(events.NewMessage(pattern=r'^/ascii\s+"?([^"]+)"?', outgoing=True))
        async def ascii_command(event):
            await self.fun_handler.handle_ascii(event)

        @self.client.on(events.NewMessage(pattern=r'^/rps\s+(камень|ножницы|бумага|rock|paper|scissors)', outgoing=True))
        async def rps_command(event):
            await self.fun_handler.handle_rps(event)

        @self.client.on(events.NewMessage(pattern=r'^/coin$', outgoing=True))
        async def coin_command(event):
            await self.fun_handler.handle_coin(event)

        @self.client.on(events.NewMessage(pattern=r'^/dice(?:\s+(\d+))?', outgoing=True))
        async def dice_command(event):
            await self.fun_handler.handle_dice(event)

        @self.client.on(events.NewMessage(pattern=r'^/8ball\s+"?([^"]+)"?', outgoing=True))
        async def ball_command(event):
            await self.fun_handler.handle_8ball(event)

        @self.client.on(events.NewMessage(pattern=r'^/random(?:\s+(\d+)(?:\s+(\d+))?)?', outgoing=True))
        async def random_command(event):
            await self.fun_handler.handle_random(event)

        @self.client.on(events.NewMessage(pattern=r'^/meme$', outgoing=True))
        async def meme_command(event):
            await self.fun_handler.handle_meme(event)

        @self.client.on(events.NewMessage(pattern=r'^/morning(?:\s+(.*))?$', outgoing=True))
        async def morning_command(event):
            await self.fun_handler.handle_morning(event)
            
        # Add quote and joke commands
        @self.client.on(events.NewMessage(pattern=r'^/addquote\s+(.+)$', outgoing=True))
        async def add_quote_command(event):
            await self.fun_handler.handle_add_quote(event)
            
        @self.client.on(events.NewMessage(pattern=r'^/addjoke\s+(.+)$', outgoing=True))
        async def add_joke_command(event):
            await self.fun_handler.handle_add_joke(event)
            
        # Interaction commands
        @self.client.on(events.NewMessage(pattern=r'^/insult(?:\s+(@?\S+))?$', outgoing=True))
        async def insult_command(event):
            # Get the target from the message
            target = event.pattern_match.group(1)
            await self.interactions_handler.send_interaction(event, "insults", target)
            
        @self.client.on(events.NewMessage(pattern=r'^/roast(?:\s+(@?\S+))?$', outgoing=True))
        async def roast_command(event):
            # Get the target from the message
            target = event.pattern_match.group(1)
            await self.interactions_handler.send_interaction(event, "roasts", target)
            
        @self.client.on(events.NewMessage(pattern=r'^/compliment(?:\s+(@?\S+))?$', outgoing=True))
        async def compliment_command(event):
            # Get the target from the message
            target = event.pattern_match.group(1)
            await self.interactions_handler.send_interaction(event, "compliments", target)
            
        @self.client.on(events.NewMessage(pattern=r'^/ship(?:\s+(@?\S+))?(?:\s+(@?\S+))?$', outgoing=True))
        async def ship_command(event):
            # Get both targets from the message
            target1 = event.pattern_match.group(1)
            target2 = event.pattern_match.group(2)
            
            # If no targets provided, show usage
            if not target1 or not target2:
                await event.edit("⚠️ Неправильное использование команды.\nИспользование: /ship @user1 @user2")
                return
                
            await self.interactions_handler.send_interaction(event, "ship", target1, target2)
            
        @self.client.on(events.NewMessage(pattern=r'^/gayrate(?:\s+(@?\S+))?$', outgoing=True))
        async def gayrate_command(event):
            # Get the target from the message
            target = event.pattern_match.group(1)
            await self.interactions_handler.send_interaction(event, "gayrate", target)
            
        @self.client.on(events.NewMessage(pattern=r'^/slap(?:\s+(@?\S+))?$', outgoing=True))
        async def slap_command(event):
            await self.fun_handler.handle_slap(event)
            
        @self.client.on(events.NewMessage(pattern=r'^/kiss(?:\s+(@?\S+))?$', outgoing=True))
        async def kiss_command(event):
            await self.fun_handler.handle_kiss(event)
            
        @self.client.on(events.NewMessage(pattern=r'^/hug(?:\s+(@?\S+))?$', outgoing=True))
        async def hug_command(event):
            await self.fun_handler.handle_hug(event)
            
        @self.client.on(events.NewMessage(pattern=r'^/commit(?:\s+(.*))?$', outgoing=True))
        async def commit_command(event):
            # Get the target (commit type and optional message) from the message
            # group(1) will be None if no arguments are provided
            target = event.pattern_match.group(1)
            await self.interactions_handler.send_interaction(event, "commit", target)

        # Утилиты
        @self.client.on(events.NewMessage(pattern=r'^/hash\s+(.+)', outgoing=True))
        async def hash_command(event):
            await self.fun_handler.handle_hash(event)
            
        @self.client.on(events.NewMessage(pattern=r'^/define(?:\s+(@?\S+))?$', outgoing=True))
        async def define_command(event):
            # Get the target (username or text) from the message
            target = event.pattern_match.group(1)
            await self.interactions_handler.send_interaction(event, "define", target)

        @self.client.on(events.NewMessage(pattern=r'^/calc\s+(.+)', outgoing=True))
        async def calc_command(event):
            await self.fun_handler.handle_calc(event)

        # Системные команды
        @self.client.on(events.NewMessage(pattern=r'^/clear\s+(\d+)', outgoing=True))
        async def clear_command(event):
            await self.system_handler.handle_clear(event)

        @self.client.on(events.NewMessage(pattern=r'^/clear\s+sender\s+(all|\d+)', outgoing=True))
        async def clear_sender_command(event):
            await self.system_handler.handle_clear_sender(event)

        @self.client.on(events.NewMessage(pattern=r'^/clear\s+user\s+(all|\d+)', outgoing=True))
        async def clear_user_command(event):
            await self.system_handler.handle_clear_user(event)

        @self.client.on(events.NewMessage(pattern=r'^/clear\s+chat$', outgoing=True))
        async def clear_chat_command(event):
            await self.system_handler.handle_clear_chat(event)

        @self.client.on(events.NewMessage(pattern=r'^/cancel\s+(timer|wake|mention|all)(?:\s+(\S+))?$', outgoing=True))
        async def cancel_command(event):
            await self.system_handler.handle_cancel(event)

        @self.client.on(events.NewMessage(pattern=r'^/list(?:\s+(timers|wake|all))?', outgoing=True))
        async def list_command(event):
            await self.system_handler.handle_list(event)

        @self.client.on(events.NewMessage(pattern=r'^/ping$', outgoing=True))
        async def ping_command(event):
            await self.system_handler.handle_ping(event)

        @self.client.on(events.NewMessage(pattern=r'^/uptime$', outgoing=True))
        async def uptime_command(event):
            await self.system_handler.handle_uptime(event, self.start_time)

        @self.client.on(events.NewMessage(pattern=r'^/stats$', outgoing=True))
        async def stats_command(event):
            await self.system_handler.handle_stats(event)

        @self.client.on(events.NewMessage(pattern=r'^/help$', outgoing=True))  
        async def help_command(event):
            await self.system_handler.handle_help(event)

        @self.client.on(events.NewMessage(pattern=r'^/stop$', outgoing=True))
        async def stop_command(event):
            await event.edit("🔴 Бот остановлен!")
            logger.info("Бот остановлен пользователем")
            await self.client.disconnect()

    async def start(self):
        """Запуск бота и всех его компонентов."""
        logger.info("Запуск клиентов Telegram...")
        # Запускаем основного бота
        await self.client.start(bot_token=os.getenv('BOT_TOKEN'))
        logger.info("Основной бот запущен.")

        # Запускаем бота-отправщика, если он есть
        if self.sender_client:
            await self.sender_client.start(bot_token=os.getenv('SENDER_BOT_API'))
            logger.info("Бот-отправщик запущен.")

        # Инициализация обработчиков после запуска клиентов
        self.timer_handler = TimerHandler(self)
        self.wake_handler = WakeHandler(self, self.sender_client or self.client)
        self.mention_handler = MentionHandler(self)
        self.fun_handler = FunHandler(self)
        self.system_handler = SystemHandler(self, self.sender_client)
        self.interactions_handler = InteractionsHandler(self)  # Initialize InteractionsHandler
        logger.info("Обработчики инициализированы.")

        # Регистрация обработчиков
        self.setup_handlers()
        logger.info("Обработчики зарегистрированы.")

        # Восстанавливаем задачи
        await self.timer_handler.restore_timers()
        await self.wake_handler.restore_alarms()
        await self.mention_handler.restore_mentions()
        logger.info("Задачи восстановлены.")

        logger.info("Персональный бот успешно запущен и готов к работе.")
        await self.client.run_until_disconnected()

    async def stop(self):
        """Остановка бота"""
        logger.info("Остановка бота...")
        if hasattr(self, 'timer_handler') and self.timer_handler.active_timers:
            print("\nБот был отключен, но все таймеры сохранены и будут восстановлены при следующем запуске.")
        await self.client.disconnect()

async def main():
    """Основная функция для запуска бота."""
    bot = PersonalBot()
    
    try:
        # Инициализация и запуск бота
        await bot.start()
    except KeyboardInterrupt:
        # Пользователь нажал Ctrl+C, выходим тихо
        print("\nБот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка в основном цикле: {e}")
        print(f"Произошла ошибка: {e}")
    finally:
        # Убедимся, что бот корректно завершает работу
        if 'bot' in locals():
            await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Дополнительная обработка на случай, если что-то пойдет не так
        print("\nБот завершает работу...")
        sys.exit(0)