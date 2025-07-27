#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telethon import TelegramClient
from telethon.tl.types import Message

from utils.json_storage import JsonStorage
from utils.time_parser import TimeParser
from config import config

logger = logging.getLogger(__name__)

class WakeHandler:
    def __init__(self, bot, sender_client):
        self.bot = bot
        self.sender_client = sender_client
        self.active_alarms: Dict[str, asyncio.Task] = {}
        self.active_reminders: Dict[str, asyncio.Task] = {}
    
    async def handle_wake(self, event):
        """Обработка команды /wake"""
        try:
            self.bot.storage.increment_command_usage('wake')
            args = event.pattern_match.group(1).strip().split()
            if not args:
                await event.edit(f"{config.ERROR_EMOJI} Используйте: /wake 10m [количество_сообщений]")
                return
            
            # Парсим время
            time_str = args[0]
            duration_td = self.bot.time_parser.parse_duration(time_str)
            
            if duration_td is None or duration_td.total_seconds() <= 0:
                await event.edit(f"{config.ERROR_EMOJI} Неверный или нулевой формат времени! Используйте: 30s, 5m, 1h")
                return
            
            if duration_td > config.MAX_TIMER_SECONDS:
                max_hours = int(config.MAX_TIMER_SECONDS.total_seconds() // 3600)
                await event.edit(f"{config.ERROR_EMOJI} Максимальное время: {max_hours} часов")
                return

            seconds = int(duration_td.total_seconds())
            
            # Парсим количество сообщений (опционально)
            message_count = config.DEFAULT_WAKE_MESSAGES
            if len(args) > 1:
                try:
                    message_count = int(args[1])
                    if message_count > config.MAX_SPAM_COUNT:
                        message_count = config.MAX_SPAM_COUNT
                        await event.reply(f"{config.WARNING_EMOJI} Максимальное количество сообщений: {config.MAX_SPAM_COUNT}")
                    elif message_count < 1:
                        message_count = 1
                except ValueError:
                    await event.edit(f"{config.ERROR_EMOJI} Неверное количество сообщений!")
                    return
            
            # Создаем уникальный ID для будильника
            alarm_id = f"wake_{event.chat_id}_{event.id}_{datetime.now().timestamp()}"
            
            # Получаем ID пользователя для отправки в ЛС
            user_id = event.sender_id
            
            # Сохраняем информацию о будильнике
            alarm_data = {
                'id': alarm_id,
                'chat_id': event.chat_id,
                'message_id': event.id,
                'user_id': user_id,
                'start_time': datetime.now().isoformat(),
                'duration': seconds,
                'message_count': message_count,
                'type': 'wake'
            }
            
            self.bot.storage.save_alarm(alarm_data)
            self.bot.storage.increment_alarms_created()
            
            # Запускаем будильник
            task = asyncio.create_task(self._run_wake_alarm(event, seconds, message_count, alarm_id, user_id))
            self.active_alarms[alarm_id] = task
            
            time_str_readable = self.bot.time_parser.seconds_to_string(seconds)
            await event.edit(f"{config.WAKE_EMOJI} Будильник установлен на {time_str_readable} ({message_count} сообщений)")
            
            logger.info(f"Установлен будильник на {seconds} секунд с {message_count} сообщениями")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_wake: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при создании будильника!")
    
    async def _run_wake_alarm(self, event, delay_seconds: int, message_count: int, alarm_id: str, user_id: int):
        """Запуск будильника"""
        try:
            # Ждем указанное время
            await asyncio.sleep(delay_seconds)
            
            # Отправляем сообщения в ЛС пользователю
            for i in range(message_count):
                try:
                    await self.sender_client.send_message(user_id, f"{config.WAKE_EMOJI} {config.DEFAULT_WAKE_TEXT}")
                    await asyncio.sleep(0.1)  # Небольшая задержка между сообщениями
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения будильника {i+1}: {e}")
            
            # Обновляем исходное сообщение
            try:
                await event.edit(f"{config.SUCCESS_EMOJI} Будильник сработал! Отправлено {message_count} сообщений в ЛС")
            except:
                pass  # Сообщение могло быть удалено
            
            # Удаляем будильник из активных
            if alarm_id in self.active_alarms:
                del self.active_alarms[alarm_id]
            
            self.bot.storage.remove_alarm(alarm_id)
        
            logger.info(f"Будильник {alarm_id} сработал успешно")
            
        except asyncio.CancelledError:
            logger.info(f"Будильник {alarm_id} был отменен")
            try:
                await event.edit(f"{config.WARNING_EMOJI} Будильник отменен")
            except:
                pass
            if alarm_id in self.active_alarms:
                del self.active_alarms[alarm_id]
            self.bot.storage.remove_alarm(alarm_id)
        except Exception as e:
            logger.error(f"Ошибка в будильнике {alarm_id}: {e}")
            try:
                await event.edit(f"{config.ERROR_EMOJI} Ошибка в будильнике!")
            except:
                pass
    
    async def handle_remind(self, event):
        """Обработка команды /remind"""
        try:
            self.bot.storage.increment_command_usage('remind')
            # Используем регулярное выражение для парсинга команды
            full_text = event.pattern_match.group(1).strip()
            
            # Пытаемся найти паттерн: время + текст в кавычках или без них
            # Поддерживаемые форматы:
            # /remind 5m "купить молоко"
            # /remind 1h текст без кавычек
            # /remind 30s "текст с пробелами"
            
            parts = full_text.split(None, 1)
            if len(parts) < 2:
                await event.edit(f"{config.ERROR_EMOJI} Используйте: /remind 5m \"текст напоминания\"")
                return
            
            time_str = parts[0]
            reminder_text = parts[1]
            
            # Убираем кавычки если есть
            if reminder_text.startswith('"') and reminder_text.endswith('"'):
                reminder_text = reminder_text[1:-1]
            elif reminder_text.startswith("'") and reminder_text.endswith("'"):
                reminder_text = reminder_text[1:-1]
            
            # Парсим время
            duration_td = self.bot.time_parser.parse_duration(time_str)
            
            if duration_td is None or duration_td.total_seconds() <= 0:
                await event.edit(f"{config.ERROR_EMOJI} Неверный или нулевой формат времени! Используйте: 30s, 5m, 1h")
                return
            
            if duration_td > config.MAX_TIMER_SECONDS:
                max_hours = int(config.MAX_TIMER_SECONDS.total_seconds() // 3600)
                await event.edit(f"{config.ERROR_EMOJI} Максимальное время: {max_hours} часов")
                return

            seconds = int(duration_td.total_seconds())
            
            if not reminder_text.strip():
                await event.edit(f"{config.ERROR_EMOJI} Текст напоминания не может быть пустым!")
                return
            
            # Создаем уникальный ID для напоминания
            reminder_id = f"remind_{event.chat_id}_{event.id}_{datetime.now().timestamp()}"
            
            # Получаем ID пользователя
            user_id = event.sender_id
            
            # Сохраняем информацию о напоминании
            reminder_data = {
                'id': reminder_id,
                'chat_id': event.chat_id,
                'message_id': event.id,
                'user_id': user_id,
                'start_time': datetime.now().isoformat(),
                'duration': seconds,
                'text': reminder_text,
                'type': 'reminder'
            }
            
            self.bot.storage.save_reminder(reminder_data)
            self.bot.storage.increment_alarms_created()
            
            # Запускаем напоминание
            task = asyncio.create_task(self._run_reminder(event, seconds, reminder_text, reminder_id, user_id))
            self.active_reminders[reminder_id] = task
            
            time_str_readable = self.bot.time_parser.seconds_to_string(seconds)
            await event.edit(f"💭 Напоминание установлено на {time_str_readable}: \"{reminder_text}\"")
            
            logger.info(f"Установлено напоминание на {seconds} секунд: {reminder_text}")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_remind: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при создании напоминания!")
    
    async def _run_reminder(self, event, delay_seconds: int, reminder_text: str, reminder_id: str, user_id: int):
        """Запуск напоминания"""
        try:
            # Ждем указанное время
            await asyncio.sleep(delay_seconds)
            
            # Отправляем напоминание в ЛС
            reminder_msg = f"{config.DEFAULT_REMINDER_TEXT} {reminder_text}"
            await self.sender_client.send_message(user_id, reminder_msg)
            
            # Обновляем исходное сообщение
            try:
                await event.edit(f"{config.SUCCESS_EMOJI} Напоминание отправлено: \"{reminder_text}\"")
            except:
                pass  # Сообщение могло быть удалено
            
            # Удаляем напоминание из активных
            if reminder_id in self.active_reminders:
                del self.active_reminders[reminder_id]
            
            self.bot.storage.remove_reminder(reminder_id)
            
            logger.info(f"Напоминание {reminder_id} отправлено успешно")
            
        except asyncio.CancelledError:
            logger.info(f"Напоминание {reminder_id} было отменено")
            try:
                await event.edit(f"{config.WARNING_EMOJI} Напоминание отменено")
            except:
                pass
            if reminder_id in self.active_reminders:
                del self.active_reminders[reminder_id]
            self.bot.storage.remove_reminder(reminder_id)
        except Exception as e:
            logger.error(f"Ошибка в напоминании {reminder_id}: {e}")
            try:
                await event.edit(f"{config.ERROR_EMOJI} Ошибка в напоминании!")
            except:
                pass
    
    async def cancel_alarm_by_id(self, alarm_id: str) -> bool:
        """Отменяет конкретный будильник по ID
        
        Args:
            alarm_id: ID будильника для отмены
            
        Returns:
            bool: True если будильник был найден и отменен, иначе False
        """
        if alarm_id in self.active_alarms:
            task = self.active_alarms[alarm_id]
            task.cancel()
            del self.active_alarms[alarm_id]
            self.bot.storage.remove_alarm(alarm_id)
            logger.info(f"Будильник {alarm_id} был отменен по запросу")
            return True
        return False
        
    async def cancel_alarms(self) -> int:
        """Отменяет все активные будильники"""
        cancelled_count = 0
        
        for alarm_id, task in list(self.active_alarms.items()):
            task.cancel()
            cancelled_count += 1
        
        self.active_alarms.clear()
        self.bot.storage.clear_alarms()
        
        return cancelled_count
    
    async def cancel_reminders(self) -> int:
        """Отменяет все активные напоминания"""
        cancelled_count = 0
        
        for reminder_id, task in list(self.active_reminders.items()):
            task.cancel()
            cancelled_count += 1
        
        self.active_reminders.clear()
        self.bot.storage.clear_reminders()
        
        return cancelled_count
    
    async def get_active_alarms(self) -> List[dict]:
        """Возвращает список активных будильников"""
        alarms = []
        
        for alarm_id in self.active_alarms.keys():
            alarm_data = self.bot.storage.get_alarm(alarm_id)
            if alarm_data:
                alarms.append(alarm_data)
        
        return alarms
    
    async def get_active_reminders(self) -> List[dict]:
        """Возвращает список активных напоминаний"""
        reminders = []
        
        for reminder_id in self.active_reminders.keys():
            reminder_data = self.bot.storage.get_reminder(reminder_id)
            if reminder_data:
                reminders.append(reminder_data)
        
        return reminders
    
    async def restore_alarms(self):
        """Восстанавливает будильники после перезапуска бота"""
        try:
            # Восстанавливаем будильники
            saved_alarms = self.bot.storage.get_all_alarms()
            for alarm_data in saved_alarms:
                alarm_id = alarm_data.get('id')
                if alarm_id:
                    await self._restore_alarm(alarm_id, alarm_data)

            # Восстанавливаем напоминания
            saved_reminders = self.bot.storage.get_all_reminders()
            for reminder_data in saved_reminders:
                reminder_id = reminder_data.get('id')
                if reminder_id:
                    await self._restore_reminder(reminder_id, reminder_data)
        
        except Exception as e:
            logger.error(f"Ошибка при восстановлении будильников: {e}")
    
    async def _restore_alarm(self, alarm_id: str, alarm_data: dict):
        """Восстанавливает отдельный будильник"""
        try:
            # Проверяем, не истек ли будильник
            start_time = datetime.fromisoformat(alarm_data['start_time'])
            elapsed = (datetime.now() - start_time).total_seconds()
            remaining = alarm_data['duration'] - elapsed
            
            if remaining <= 0:
                # Будильник уже должен был сработать
                self.bot.storage.remove_alarm(alarm_id)
                return
            
            # Обновляем будильник с оставшимся временем и сохраняем
            alarm_data['duration'] = int(remaining)
            alarm_data['start_time'] = datetime.now().isoformat()
            self.bot.storage.save_alarm(alarm_data)

            # Восстанавливаем будильник с оставшимся временем
            chat_id = alarm_data['chat_id']
            message_id = alarm_data['message_id']
            user_id = alarm_data['user_id']
            message_count = alarm_data.get('message_count', config.DEFAULT_WAKE_MESSAGES)
            
            # Получаем сообщение
            try:
                message = await self.bot.client.get_messages(chat_id, ids=message_id)
                if message:
                    # Создаем задачу для оставшегося времени
                    task = asyncio.create_task(
                        self._run_wake_alarm(message, int(remaining), message_count, alarm_id, user_id)
                    )
                    self.active_alarms[alarm_id] = task
                    
                    logger.info(f"Восстановлен будильник {alarm_id} с {remaining:.0f} секунд")
                else:
                    self.bot.storage.remove_alarm(alarm_id)
            except Exception as e:
                logger.error(f"Ошибка получения сообщения для будильника {alarm_id}: {e}")
                self.bot.storage.remove_alarm(alarm_id)
                
        except Exception as e:
            logger.error(f"Ошибка восстановления будильника {alarm_id}: {e}")
            self.bot.storage.remove_alarm(alarm_id)
    
    async def _restore_reminder(self, reminder_id: str, reminder_data: dict):
        """Восстанавливает отдельное напоминание"""
        try:
            # Проверяем, не истекло ли напоминание
            start_time = datetime.fromisoformat(reminder_data['start_time'])
            elapsed = (datetime.now() - start_time).total_seconds()
            remaining = reminder_data['duration'] - elapsed
            
            if remaining <= 0:
                # Напоминание уже должно было сработать
                self.bot.storage.remove_reminder(reminder_id)
                return
            
            # Обновляем напоминание с оставшимся временем и сохраняем
            reminder_data['duration'] = int(remaining)
            reminder_data['start_time'] = datetime.now().isoformat()
            self.bot.storage.save_reminder(reminder_data)

            # Восстанавливаем напоминание с оставшимся временем
            chat_id = reminder_data['chat_id']
            message_id = reminder_data['message_id']
            user_id = reminder_data['user_id']
            reminder_text = reminder_data.get('text', 'Напоминание')
            
            # Получаем сообщение
            try:
                message = await self.bot.client.get_messages(chat_id, ids=message_id)
                if message:
                    # Создаем задачу для оставшегося времени
                    task = asyncio.create_task(
                        self._run_reminder(message, int(remaining), reminder_text, reminder_id, user_id)
                    )
                    self.active_reminders[reminder_id] = task
                    
                    logger.info(f"Восстановлено напоминание {reminder_id} с {remaining:.0f} секунд")
                else:
                    self.bot.storage.remove_reminder(reminder_id)
            except Exception as e:
                logger.error(f"Ошибка получения сообщения для напоминания {reminder_id}: {e}")
                self.bot.storage.remove_reminder(reminder_id)
                
        except Exception as e:
            logger.error(f"Ошибка восстановления напоминания {reminder_id}: {e}")
            self.bot.storage.remove_reminder(reminder_id)