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
    def __init__(self, bot, sender_client=None):
        self.bot = bot
        self.sender_client = sender_client
    
    async def handle_cancel(self, event):
        """Обработка команды /cancel"""
        try:
            self.bot.storage.increment_command_usage('cancel')
            
            cancel_type = event.pattern_match.group(1).strip().lower()
            target_id = event.pattern_match.group(2)
            
            if target_id:  # Если указан ID для отмены
                result = None
                if cancel_type == 'timer':
                    # Пытаемся найти таймер по номеру из списка
                    try:
                        # Получаем список активных таймеров
                        timers = await self.bot.timer_handler.get_active_timers()
                        
                        # Пробуем преобразовать введенный ID в число (индекс в списке)
                        try:
                            index = int(target_id) - 1  # Пользователь вводит начиная с 1
                            if 0 <= index < len(timers):
                                # Находим таймер по индексу
                                timer_to_cancel = timers[index]
                                result = await self.bot.timer_handler.cancel_timer_by_id(timer_to_cancel['id'])
                            else:
                                await event.edit(f"{config.ERROR_EMOJI} Неверный номер таймера. Используйте /list timers для просмотра активных таймеров")
                                return
                        except ValueError:
                            # Если введен не числовой ID, ищем по полному ID
                            found = False
                            for timer in timers:
                                if timer.get('id') == target_id:
                                    result = await self.bot.timer_handler.cancel_timer_by_id(timer['id'])
                                    found = True
                                    break
                            if not found:
                                await event.edit(f"{config.ERROR_EMOJI} Не найден таймер с ID: {target_id}")
                                return
                    except Exception as e:
                        logger.error(f"Ошибка при отмене таймера: {e}")
                        await event.edit(f"{config.ERROR_EMOJI} Произошла ошибка при отмене таймера")
                        return
                        
                elif cancel_type == 'wake':
                    # Обработка отмены будильников/напоминаний по номеру
                    try:
                        alarms = await self.bot.wake_handler.get_active_alarms()
                        reminders = await self.bot.wake_handler.get_active_reminders()
                        all_wake = alarms + reminders
                        
                        try:
                            index = int(target_id) - 1
                            if 0 <= index < len(all_wake):
                                item = all_wake[index]
                                if index < len(alarms):
                                    result = await self.bot.wake_handler.cancel_alarm_by_id(item['id'])
                                else:
                                    result = await self.bot.wake_handler.cancel_reminder_by_id(item['id'])
                            else:
                                await event.edit(f"{config.ERROR_EMOJI} Неверный номер. Используйте /list wake для просмотра активных будильников и напоминаний")
                                return
                        except ValueError:
                            # Если введен не числовой ID, ищем по полному ID
                            found = False
                            for item in all_wake:
                                if item.get('id') == target_id:
                                    if item in alarms:
                                        result = await self.bot.wake_handler.cancel_alarm_by_id(item['id'])
                                    else:
                                        result = await self.bot.wake_handler.cancel_reminder_by_id(item['id'])
                                    found = True
                                    break
                            if not found:
                                await event.edit(f"{config.ERROR_EMOJI} Не найден будильник/напоминание с ID: {target_id}")
                                return
                    except Exception as e:
                        logger.error(f"Ошибка при отмене будильника/напоминания: {e}")
                        await event.edit(f"{config.ERROR_EMOJI} Произошла ошибка при отмене")
                        return
                        
                elif cancel_type == 'mention':
                    # Обработка отмены упоминаний/спама по номеру
                    try:
                        mentions = await self.bot.mention_handler.get_active_mentions()
                        
                        try:
                            index = int(target_id) - 1
                            if 0 <= index < len(mentions):
                                mention = mentions[index]
                                result = await self.bot.mention_handler.cancel_mention_by_id(mention['id'])
                            else:
                                await event.edit(f"{config.ERROR_EMOJI} Неверный номер. Используйте /list mention для просмотра активных упоминаний")
                                return
                        except ValueError:
                            # Если введен не числовой ID, ищем по полному ID
                            found = False
                            for mention in mentions:
                                if mention.get('id') == target_id:
                                    result = await self.bot.mention_handler.cancel_mention_by_id(mention['id'])
                                    found = True
                                    break
                            if not found:
                                await event.edit(f"{config.ERROR_EMOJI} Не найдено упоминание с ID: {target_id}")
                                return
                    except Exception as e:
                        logger.error(f"Ошибка при отмене упоминания: {e}")
                        await event.edit(f"{config.ERROR_EMOJI} Произошла ошибка при отмене упоминания")
                        return
                        
                else:
                    await event.edit(f"{config.ERROR_EMOJI} Отмена по номеру доступна только для: timer, wake, mention")
                    return
                
                if result:
                    await event.edit(f"{config.SUCCESS_EMOJI} Успешно отменено: {cancel_type} {target_id}")
                else:
                    await event.edit(f"{config.ERROR_EMOJI} Не удалось отменить {cancel_type} с номером: {target_id}")
                return
                
            # Стандартная отмена (всех таймеров/будильников/упоминаний)
            cancelled_count = 0
            
            if cancel_type == 'timer':
                cancelled_count = await self.bot.timer_handler.cancel_timers()
                await event.edit(f"{config.SUCCESS_EMOJI} Отменено {cancelled_count} таймеров")
                
            elif cancel_type == 'wake':
                alarm_count = await self.bot.wake_handler.cancel_alarms()
                reminder_count = await self.bot.wake_handler.cancel_reminders()
                cancelled_count = alarm_count + reminder_count
                await event.edit(f"{config.SUCCESS_EMOJI} Отменено {alarm_count} будильников и {reminder_count} напоминаний")
                
            elif cancel_type == 'mention':
                cancelled_count = await self.bot.mention_handler.cancel_mentions()
                await event.edit(f"{config.SUCCESS_EMOJI} Отменено {cancelled_count} упоминаний/спама")
                
            elif cancel_type == 'all':
                timer_count = await self.bot.timer_handler.cancel_timers()
                alarm_count = await self.bot.wake_handler.cancel_alarms()
                reminder_count = await self.bot.wake_handler.cancel_reminders()
                mention_count = await self.bot.mention_handler.cancel_mentions()
                
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
            self.bot.storage.increment_command_usage('list')
            
            list_type = 'all'
            match = event.pattern_match.group(1)
            if match:
                list_type = match.strip().lower()
            
            message_parts = []
            
            if list_type in ['timers', 'all']:
                timers = await self.bot.timer_handler.get_active_timers()
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
                alarms = await self.bot.wake_handler.get_active_alarms()
                reminders = await self.bot.wake_handler.get_active_reminders()
                
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
                mentions = await self.bot.mention_handler.get_active_mentions()
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
            self.bot.storage.increment_command_usage('ping')
            
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
            self.bot.storage.increment_command_usage('uptime')
            
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
            self.bot.storage.increment_command_usage('stats')
            
            stats = self.bot.storage.get_stats()
            
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
            self.bot.storage.increment_command_usage('help')
            
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
• `/addquote "цитата"` - добавить новую цитату
• `/joke` - случайная шутка  
• `/addjoke "шутка"` - добавить новую шутку
• `/slap [@username | текст]` - ударить кого-то
• `/kiss [@username | текст]` - поцеловать кого-то
• `/hug [@username | текст]` - обнять кого-то
• `/ship [@user1 @user2 | текст текст]` - шиперить двух пользователей
• `/roast [@username | текст]` - выдать оскорбление в адрес цели
• `/insult [@username | текст]` - жёстко пошутить над целью
• `/ascii "HELLO"` - ASCII арт
• `/rps камень` - камень-ножницы-бумага
• `/coin` - подбросить монетку
• `/dice 20` - бросить кубик (1-20)
• `/8ball "вопрос?"` - магический шар
• `/random 1 100` - случайное число
• `/meme` - случайный мем
• `/morning [1-3]` - утреннее сообщение (1 - общий, 2 - для друзей/кентов, 3 - для девушки/подруги)

🧮 **Утилиты:**
• `/calc 2+2*5` - калькулятор
• `/hash "текст"` - MD5 хеш
• `/hash sha256 "текст"` - SHA256 хеш

⚙️ **Управление:**
• `/cancel timer` - отменить все таймеры
• `/cancel timer <id>` - отменить конкретный таймер по ID
• `/cancel wake` - отменить все будильники
• `/cancel wake <id>` - отменить конкретный будильник по ID
• `/cancel mention` - отменить все упоминания
• `/cancel mention <id>` - отменить конкретное упоминание по ID
• `/cancel all` - отменить всё
• `/clear 10` - удалить 10 своих сообщений
• `/clear sender 10` - удалить 10 сообщений от бота-отправщика
• `/clear sender all` - удалить все сообщения от бота-отправщика
• `/clear user 10` - удалить 10 сообщений пользователя (ответом на сообщение)
• `/clear chat` - очистить весь чат (нужны права администратора)
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
            
            logger.info(f"Показана справка")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_help: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при показе справки!")

    async def handle_clear_sender(self, event):
        """Очищает сообщения от бота-отправщика."""
        if not self.sender_client:
            await event.edit(f"{config.ERROR_EMOJI} Бот-отправщик не настроен.")
            return

        try:
            param = event.pattern_match.group(1)
            sender_bot_me = await self.sender_client.get_me()
            sender_id = sender_bot_me.id

            messages_to_delete = []
            if param == 'all':
                limit = None  # Telethon's None means no limit
                feedback_msg = f"{config.SUCCESS_EMOJI} Все сообщения от бота-отправщика удаляются..."
            else:
                limit = int(param)
                feedback_msg = f"{config.SUCCESS_EMOJI} Удаляю {limit} сообщений от бота-отправщика..."
            
            await event.edit(feedback_msg)

            async for message in self.bot.client.iter_messages(event.chat_id, from_user=sender_id):
                messages_to_delete.append(message.id)
                if limit is not None and len(messages_to_delete) >= limit:
                    break

            if messages_to_delete:
                await self.bot.client.delete_messages(event.chat_id, messages_to_delete)
                final_msg = f"{config.SUCCESS_EMOJI} Удалено {len(messages_to_delete)} сообщений от бота-отправщика."
                logger.info(f"Удалено {len(messages_to_delete)} сообщений от бота-отправщика {sender_id} в чате {event.chat_id}")
            else:
                final_msg = f"{config.INFO_EMOJI} Не найдено сообщений от бота-отправщика для удаления."

            await event.edit(final_msg)
            await asyncio.sleep(5) # Даем пользователю время прочитать
            await event.delete()

        except Exception as e:
            logger.error(f"Ошибка при очистке сообщений от отправителя: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Произошла ошибка при очистке сообщений.")

    async def handle_clear_user(self, event):
        """Очищает сообщения конкретного пользователя (в ответ на его сообщение)."""
        replied_msg = await event.get_reply_message()
        if not replied_msg:
            await event.edit(f"{config.ERROR_EMOJI} Используйте эту команду в ответ на сообщение пользователя.")
            return
        try:
            # Проверяем, что это сообщение от пользователя
            if not hasattr(replied_msg, 'sender_id'):
                logger.warning("У сообщения нет атрибута sender_id")
                await event.edit(f"{config.ERROR_EMOJI} Не удалось определить отправителя. Попробуйте другое сообщение.")
                return
                
            param = event.pattern_match.group(1)
            user_to_clear_id = replied_msg.sender_id
            
            # Проверяем, что это ID пользователя, а не чата/канала
            if user_to_clear_id is None or (hasattr(user_to_clear_id, 'channel_id') or hasattr(user_to_clear_id, 'chat_id')):
                logger.warning(f"Отправитель не является пользователем: {user_to_clear_id}")
                await event.edit(f"{config.ERROR_EMOJI} Это сообщение не от пользователя. Попробуйте снова, ответив на обычное сообщение пользователя.")
                return

            messages_to_delete = []
            if param == 'all':
                limit = None
                feedback_msg = f"{config.SUCCESS_EMOJI} Удаляю все сообщения от пользователя..."
            else:
                limit = int(param)
                feedback_msg = f"{config.SUCCESS_EMOJI} Удаляю {limit} сообщений от пользователя..."

            await event.edit(feedback_msg)

            async for message in self.bot.client.iter_messages(event.chat_id, from_user=user_to_clear_id):
                messages_to_delete.append(message.id)
                if limit is not None and len(messages_to_delete) >= limit:
                    break

            if messages_to_delete:
                await self.bot.client.delete_messages(event.chat_id, messages_to_delete)
                final_msg = f"{config.SUCCESS_EMOJI} Удалено {len(messages_to_delete)} сообщений."
                logger.info(f"Удалено {len(messages_to_delete)} сообщений от {user_to_clear_id} в чате {event.chat_id}")
            else:
                final_msg = f"{config.INFO_EMOJI} Не найдено сообщений от этого пользователя."

            await event.edit(final_msg)
            await asyncio.sleep(5)
            await event.delete()

        except Exception as e:
            logger.error(f"Ошибка при очистке сообщений пользователя: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Произошла ошибка.")

    async def handle_clear_chat(self, event):
        """Очищает весь чат (нужны права администратора)."""
        try:
            await event.edit(f"{config.WARNING_EMOJI} **ВНИМАНИЕ!** Начинаю полную очистку чата... Это может занять время.")
            
            # Получаем все ID сообщений, кроме нашего сообщения с командой
            message_ids = [msg.id async for msg in self.bot.client.iter_messages(event.chat_id) if msg.id != event.id]
            
            if not message_ids:
                await event.edit(f"{config.INFO_EMOJI} Чат уже пуст.")
                return

            # Удаляем сообщения пачками по 100
            total_deleted = 0
            for i in range(0, len(message_ids), 100):
                chunk = message_ids[i:i + 100]
                await self.bot.client.delete_messages(event.chat_id, chunk)
                total_deleted += len(chunk)
                await asyncio.sleep(1) # Небольшая задержка, чтобы не словить флуд

            final_msg = f"{config.SUCCESS_EMOJI} Чат очищен! Удалено {total_deleted} сообщений."
            logger.info(f"Полная очистка чата {event.chat_id}. Удалено {total_deleted} сообщений.")
            # Отправляем финальное сообщение и затем удаляем его и исходную команду
            final_msg_entity = await self.bot.client.send_message(event.chat_id, final_msg)
            await asyncio.sleep(10)
            await self.bot.client.delete_messages(event.chat_id, [event.id, final_msg_entity.id])

        except Exception as e:
            logger.error(f"Ошибка при полной очистке чата: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Не удалось очистить чат. Убедитесь, что у меня есть права администратора.")

    async def handle_clear(self, event):
        """Обработка команды /clear {количество}"""
        try:
            self.bot.storage.increment_command_usage('clear')
            
            match = event.pattern_match.group(1)
            if not match or not match.strip().isdigit():
                await event.edit(f"{config.ERROR_EMOJI} Укажите количество: `/clear 10`")
                return

            count = int(match.strip())
            if count <= 0:
                await event.edit(f"{config.ERROR_EMOJI} Количество должно быть больше нуля.")
                return

            if count > 100:
                await event.edit(f"{config.WARNING_EMOJI} Можно удалить максимум 100 сообщений за раз.")
                count = 100

            # Собираем ID наших сообщений для удаления
            user_id = event.sender_id
            message_ids_to_delete = []
            
            # Ищем сообщения для удаления, включая команду
            # Ищем с запасом, чтобы найти нужное количество именно ваших сообщений
            async for message in self.bot.client.iter_messages(event.chat_id, limit=count * 5, from_user=user_id):
                if len(message_ids_to_delete) >= count + 1: # +1 чтобы удалить и команду /clear
                    break
                message_ids_to_delete.append(message.id)

            # Удаляем сообщения
            if message_ids_to_delete:
                await self.bot.client.delete_messages(event.chat_id, message_ids_to_delete)
                deleted_count = len(message_ids_to_delete)
                
                # Отправляем временное подтверждение, так как исходное сообщение удалено
                confirmation = await self.bot.client.send_message(event.chat_id, f"{config.SUCCESS_EMOJI} Удалено {deleted_count - 1} ваших сообщений.")
                logger.info(f"Удалено {deleted_count - 1} сообщений пользователя {user_id} в чате {event.chat_id}")
                
                await asyncio.sleep(3)
                await confirmation.delete()
            else:
                await event.edit(f"{config.INFO_EMOJI} Не найдено сообщений для удаления.")

        except Exception as e:
            logger.error(f"Ошибка в handle_clear: {e}")
            # Не можем редактировать, так как сообщение может быть уже удалено
            await self.bot.client.send_message(event.chat_id, f"{config.ERROR_EMOJI} Ошибка при удалении сообщений!")

    async def handle_backup(self, event):
        """Обработка команды /backup (скрытая команда)"""
        try:
            backup_dir = await self.bot.storage.create_backup()
            
            if backup_dir:
                await event.edit(f"{config.SUCCESS_EMOJI} Резервная копия создана в папке: `{backup_dir}`")
                logger.info(f"Создана резервная копия: {backup_dir}")
            else:
                await event.edit(f"{config.ERROR_EMOJI} Ошибка создания резервной копии!")
                
        except Exception as e:
            logger.error(f"Ошибка в handle_backup: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при создании резервной копии!")