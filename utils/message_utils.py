#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telethon import TelegramClient

from utils.json_storage import JsonStorage
from config import config

logger = logging.getLogger(__name__)

class SystemHandler:
    def __init__(self, client: TelegramClient, storage: JsonStorage):
        self.client = client
        self.storage = storage
    
    async def handle_cancel(self, event):
        """Обработка команды /cancel"""
        try:
            await self.storage.increment_command_usage('cancel')
            
            cancel_type = event.pattern_match.group(1).strip().lower()
            
            # Получаем обработчики из основного класса бота
            # Это нужно сделать через глобальные переменные или dependency injection
            from main import bot_instance  # Временное решение
            
            cancelled_count = 0
            
            if cancel_type == 'timer':
                cancelled_count = await bot_instance.timer_handler.cancel_timers()
                await event.edit(f"{config.SUCCESS_EMOJI} Отменено {cancelled_count} таймеров")
                
            elif cancel_type == 'wake':
                alarm_count = await bot_instance.wake_handler.cancel_alarms()
                reminder_count = await bot_instance.wake_handler.cancel_reminders()
                cancelled_count = alarm_count + reminder_count
                await event.edit(f"{config.SUCCESS_EMOJI} Отменено {alarm_count} будильников и {reminder_count} напоминаний")
                
            elif cancel_type == 'mention':
                cancelled_count = await bot_instance.mention_handler.cancel_mentions()
                await event.edit(f"{config.SUCCESS_EMOJI} Отменено {cancelled_count} упоминаний/спама")
                
            elif cancel_type == 'all':
                timer_count = await bot_instance.timer_handler.cancel_timers()
                alarm_count = await bot_instance.wake_handler.cancel_alarms()
                reminder_count = await bot_instance.wake_handler.cancel_reminders()
                mention_count = await bot_instance.mention_handler.cancel_mentions()
                
                total_count = timer_count + alarm_count + reminder_count + mention_count
                
                message = f"""
{config.SUCCESS_EMOJI} **Отменено всё:**
• Таймеры: {timer_count}
• Будильники: {alarm_count}  
• Напоминания: {reminder_count}
• Упоминания/спам: {mention_count}

**Всего: {total_count}**
                """.strip()
                
                await event.edit(message)
            else:
                await event.edit(f"{config.ERROR_EMOJI} Неизвестный тип: {cancel_type}")
                return
            
            logger.info(f"Отменено {cancelled_count} задач типа {cancel_type}")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_cancel: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при отмене!")
    
    async def handle_list(self, event):
        """Обработка команды /list"""
        try:
            await self.storage.increment_command_usage('list')
            
            list_type = 'all'
            match = event.pattern_match.group(1)
            if match:
                list_type = match.strip().lower()
            
            from main import bot_instance  # Временное решение
            
            message_parts = []
            
            if list_type in ['timers', 'all']:
                timers = await bot_instance.timer_handler.get_active_timers()
                if timers:
                    message_parts.append(f"⏰ **Активные таймеры ({len(timers)}):**")
                    for i, timer in enumerate(timers[:5], 1):  # Показываем максимум 5
                        start_time = datetime.fromisoformat(timer['start_time'])
                        elapsed = (datetime.now() - start_time).total_seconds()
                        remaining = timer['duration'] - elapsed
                        
                        if remaining > 0:
                            remaining_str = self._format_time(int(remaining))
                            message_parts.append(f"  {i}. Осталось {remaining_str}")
                        else:
                            message_parts.append(f"  {i}. Должен был закончиться")
                else:
                    if list_type == 'timers':
                        message_parts.append("⏰ Активных таймеров нет")
            
            if list_type in ['wake', 'all']:
                alarms = await bot_instance.wake_handler.get_active_alarms()
                reminders = await bot_instance.wake_handler.get_active_reminders()
                
                total_wake = len(alarms) + len(reminders)
                if total_wake > 0:
                    message_parts.append(f"\n🔔 **Будильники и напоминания ({total_wake}):**")
                    
                    # Будильники
                    for i, alarm in enumerate(alarms[:3], 1):
                        start_time = datetime.fromisoformat(alarm['start_time'])
                        elapsed = (datetime.now() - start_time).total_seconds()
                        remaining = alarm['duration'] - elapsed
                        
                        if remaining > 0:
                            remaining_str = self._format_time(int(remaining))
                            message_parts.append(f"  {i}. 🔔 Будильник через {remaining_str}")
                    
                    # Напоминания
                    for i, reminder in enumerate(reminders[:3], len(alarms) + 1):
                        start_time = datetime.fromisoformat(reminder['start_time'])
                        elapsed = (datetime.now() - start_time).total_seconds()
                        remaining = reminder['duration'] - elapsed
                        
                        if remaining > 0:
                            remaining_str = self._format_time(int(remaining))
                            text = reminder.get('text', 'Напоминание')
                            short_text = text[:30] + "..." if len(text) > 30 else text
                            message_parts.append(f"  {i}. 💭 {short_text} через {remaining_str}")
                else:
                    if list_type == 'wake':
                        message_parts.append("🔔 Активных будильников нет")
            
            if list_type in ['mention', 'all']:
                mentions = await bot_instance.mention_handler.get_active_mentions()
                if mentions:
                    message_parts.append(f"\n👤 **Активные упоминания/спам ({len(mentions)}):**")
                    for i, mention in enumerate(mentions[:3], 1):
                        if mention['type'] == 'mention':
                            username = mention.get('username', 'пользователь')
                            count = mention.get('count', 0)
                            message_parts.append(f"  {i}. Упоминания {username} ({count} раз)")
                        else:  # spam
                            text = mention.get('text', 'текст')
                            short_text = text[:20] + "..." if len(text) > 20 else text
                            count = mention.get('count', 0)
                            message_parts.append(f"  {i}. Спам \"{short_text}\" ({count} раз)")
                else:
                    if list_type == 'mention':
                        message_parts.append("👤 Активных упоминаний нет")
            
            if not message_parts:
                message = f"{config.INFO_EMOJI} Активных задач нет"
            else:
                message = "\n".join(message_parts)
                
                # Добавляем подсказку если список обрезан
                total_items = len(message_parts) - message_parts.count("")
                if total_items > 10:  # Приблизительная оценка
                    message += f"\n\n{config.INFO_EMOJI} Показаны только первые элементы"
            
            await event.edit(message)
            
            logger.info(f"Показан список: {list_type}")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_list: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при получении списка!")
    
    def _format_time(self, seconds: int) -> str:
        """Форматирует время в читаемый вид"""
        if seconds < 60:
            return f"{seconds}с"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}м {secs}с" if secs > 0 else f"{minutes}м"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}ч {minutes}м"
            else:
                return f"{hours}ч"
    
    async def handle_ping(self, event):
        """Обработка команды /ping"""
        try:
            await self.storage.increment_command_usage('ping')
            
            start_time = time.time()
            
            # Отправляем сообщение и засекаем время
            message = await event.edit("🏓 Pong!")
            
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            
            # Обновляем сообщение с временем отклика
            await message.edit(f"🏓 Pong! `{response_time}ms`")
            
            logger.info(f"Ping: {response_time}ms")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_ping: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при проверке пинга!")
    
    async def handle_uptime(self, event, start_time: datetime):
        """Обработка команды /uptime"""
        try:
            await self.storage.increment_command_usage('uptime')
            
            uptime = datetime.now() - start_time
            days = uptime.days
            hours = uptime.seconds // 3600
            minutes = (uptime.seconds % 3600) // 60
            seconds = uptime.seconds % 60
            
            uptime_parts = []
            if days > 0:
                uptime_parts.append(f"{days}д")
            if hours > 0:
                uptime_parts.append(f"{hours}ч")
            if minutes > 0:
                uptime_parts.append(f"{minutes}м")
            if seconds > 0 or not uptime_parts:
                uptime_parts.append(f"{seconds}с")
            
            uptime_str = " ".join(uptime_parts)
            
            message = f"""
🕐 **Время работы бота**

⏰ Запущен: {start_time.strftime('%d.%m.%Y %H:%M:%S')}
⌛ Работает: {uptime_str}
            """.strip()
            
            await event.edit(message)
            
            logger.info(f"Uptime: {uptime_str}")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_uptime: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при получении времени работы!")
    
    async def handle_stats(self, event):
        """Обработка команды /stats"""
        try:
            await self.storage.increment_command_usage('stats')
            
            stats = await self.storage.get_stats()
            
            # Топ команд
            commands = stats.get('commands_used', {})
            if commands:
                sorted_commands = sorted(commands.items(), key=lambda x: x[1], reverse=True)
                top_commands = sorted_commands[:5]
                
                top_commands_str = []
                for cmd, count in top_commands:
                    top_commands_str.append(f"  • /{cmd}: {count}")
            else:
                top_commands_str = ["  • Нет данных"]
            
            # Счетчики
            total_commands = stats.get('total_commands', 0)
            timers_created = stats.get('timers_created', 0)
            alarms_created = stats.get('alarms_created', 0)
            mentions_created = stats.get('mentions_created', 0)
            
            # Время последней команды
            last_command = stats.get('last_command_time')
            if last_command:
                last_command_dt = datetime.fromisoformat(last_command)
                last_command_str = last_command_dt.strftime('%d.%m.%Y %H:%M:%S')
            else:
                last_command_str = "Никогда"
            
            message = f"""
📊 **Статистика бота**

📈 **Общее:**
• Всего команд: {total_commands}
• Таймеров создано: {timers_created}
• Будильников: {alarms_created}
• Упоминаний: {mentions_created}

🏆 **Топ команд:**
{chr(10).join(top_commands_str)}

🕐 **Последняя команда:** {last_command_str}
            """.strip()
            
            await event.edit(message)
            
            logger.info("Показана статистика")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_stats: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при получении статистики!")
    
    async def handle_help(self, event):
        """Обработка команды /help"""
        try:
            await self.storage.increment_command_usage('help')
            
            help_text = f"""
🤖 **Персональный Telegram Бот**

⏰ **Таймеры:**
• `/timer 30s` - таймер с обратным отсчетом
• `/timer 5m 100` - таймер + спам 100 сообщений
• `/countdown 60` - простой обратный отсчет

🔔 **Будильники:**
• `/wake 10m` - будильник (10 сообщений в ЛС)
• `/wake 30m 50` - будильник с 50 сообщениями
• `/remind 5m "купить молоко"` - напоминание

👥 **Упоминания:**
• `/mention @user 30` - упомянуть 30 раз
• `/mention @user 5 2s` - с интервалом 2с
• `/spam "текст" 10` - спам текстом
• `/spam @user "привет" 5` - спам пользователю

🎭 **Развлечения:**
• `/quote` - случайная цитата
• `/joke` - случайная шутка  
• `/ascii "HELLO"` - ASCII арт
• `/rps камень` - камень-ножницы-бумага
• `/coin` - подбросить монетку
• `/dice 20` - бросить кубик (1-20)
• `/8ball "вопрос?"` - магический шар
• `/random 1 100` - случайное число
• `/meme` - случайный мем

🧮 **Утилиты:**
• `/calc 2+2*5` - калькулятор
• `/hash "текст"` - MD5 хеш
• `/hash sha256 "текст"` - SHA256 хеш

⚙️ **Управление:**
• `/cancel timer` - отменить таймеры
• `/cancel wake` - отменить будильники
• `/cancel mention` - отменить упоминания
• `/cancel all` - отменить всё
• `/list all` - список активных задач
• `/ping` - проверка скорости
• `/uptime` - время работы
• `/stats` - статистика команд
• `/help` - эта справка
• `/stop` - остановка бота

📖 **Единицы времени:**
• `s` - секунды (30s)
• `m` - минуты (5m)
• `h` - часы (2h)  
• `d` - дни (1d)

{config.INFO_EMOJI} Бот работает только с вашими сообщениями!
            """.strip()
            
            await event.edit(help_text)
            
            logger.info("Показана справка")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_help: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при показе справки!")
    
    async def handle_backup(self, event):
        """Обработка команды /backup (скрытая команда)"""
        try:
            backup_dir = await self.storage.create_backup()
            
            if backup_dir:
                await event.edit(f"{config.SUCCESS_EMOJI} Резервная копия создана в папке: `{backup_dir}`")
                logger.info(f"Создана резервная копия: {backup_dir}")
            else:
                await event.edit(f"{config.ERROR_EMOJI} Ошибка создания резервной копии!")
                
        except Exception as e:
            logger.error(f"Ошибка в handle_backup: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при создании резервной копии!")