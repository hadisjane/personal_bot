#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telethon import TelegramClient
from telethon.tl.types import Message

from utils.json_storage import JsonStorage
from utils.time_parser import TimeParser
from config import config

logger = logging.getLogger(__name__)

class TimerHandler:
    def __init__(self, bot):
        self.bot = bot
        self.active_timers: Dict[str, asyncio.Task] = {}
    
    async def handle_timer(self, event):
        """Обработка команды /timer"""
        try:
            args = event.pattern_match.group(1).strip().split()
            if not args:
                await event.edit(f"{config.ERROR_EMOJI} Используйте: /timer 30s [количество_спама]")
                return
            
            # Парсим время
            time_str = args[0]
            duration_td = self.bot.time_parser.parse_duration(time_str)

            if duration_td is None or duration_td.total_seconds() <= 0:
                await event.edit(f"{config.ERROR_EMOJI} Неверный или нулевой формат времени! Используйте: 30s, 5m, 1h")
                return

            if duration_td > config.MAX_TIMER_SECONDS:
                max_hours = int(config.MAX_TIMER_SECONDS.total_seconds() // 3600)
                await event.edit(f"{config.ERROR_EMOJI} Максимальное время таймера: {max_hours} часов")
                return
            
            seconds = int(duration_td.total_seconds())

            # Парсим количество спама (опционально)
            spam_count = 1
            if len(args) > 1:
                try:
                    spam_count = int(args[1])
                    if spam_count > config.MAX_SPAM_COUNT:
                        spam_count = config.MAX_SPAM_COUNT
                        await event.reply(f"{config.WARNING_EMOJI} Максимальное количество сообщений: {config.MAX_SPAM_COUNT}")
                except ValueError:
                    await event.edit(f"{config.ERROR_EMOJI} Неверное количество сообщений!")
                    return

            # Создаем уникальный ID для таймера
            timer_id = f"timer_{event.chat_id}_{event.id}_{datetime.now().timestamp()}"
            
            # Сохраняем информацию о таймере
            timer_data = {
                'id': timer_id,
                'chat_id': event.chat_id,
                'message_id': event.id,
                'start_time': datetime.now().isoformat(),
                'duration': seconds,
                'spam_count': spam_count,
                'type': 'timer'
            }
            
            self.bot.storage.save_timer(timer_data)
            
            # Запускаем таймер
            task = asyncio.create_task(self._run_timer(event, seconds, spam_count, timer_id))
            self.active_timers[timer_id] = task
            self.bot.storage.increment_timers_created()
            
            logger.info(f"Запущен таймер на {seconds} секунд с {spam_count} сообщениями")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_timer: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при создании таймера!")
    
    async def _run_timer(self, event, total_seconds: int, spam_count: int, timer_id: str):
        """Запуск таймера с обратным отсчетом"""
        try:
            original_time_str = self.bot.time_parser.seconds_to_string(total_seconds)
            
            # Обновляем сообщение на начальное
            await event.edit(f"{config.TIMER_EMOJI} Запускаю таймер на {original_time_str}")
            await asyncio.sleep(1)
            
            # Обратный отсчет
            remaining = total_seconds
            last_update = 0
            
            while remaining > 0:
                # Определяем интервал обновления (чаще в конце)
                if remaining <= 10:
                    update_interval = 1
                elif remaining <= 60:
                    update_interval = 5
                elif remaining <= 300:  # 5 минут
                    update_interval = 15
                else:
                    update_interval = 60
                
                # Обновляем сообщение только если прошел нужный интервал
                if remaining != total_seconds and (last_update == 0 or last_update - remaining >= update_interval):
                    time_str = self.bot.time_parser.seconds_to_string(remaining)
                    await event.edit(f"{config.TIMER_EMOJI} Осталось {time_str}...")
                    last_update = remaining
                
                await asyncio.sleep(1)
                remaining -= 1
            
            # Таймер закончился
            await event.edit(f"{config.SUCCESS_EMOJI} {config.DEFAULT_TIMER_END_TEXT}")
            
            # Спамим сообщениями если нужно
            if spam_count > 1:
                for i in range(spam_count - 1):  # -1 потому что одно уже отправили
                    await event.reply(f"{config.SUCCESS_EMOJI} {config.DEFAULT_TIMER_END_TEXT}")
                    await asyncio.sleep(0.1)  # Небольшая задержка чтобы не забанили
            
            # Удаляем таймер из активных
            if timer_id in self.active_timers:
                del self.active_timers[timer_id]
            
            self.bot.storage.remove_timer(timer_id)
            
            logger.info(f"Таймер {timer_id} завершен успешно")
            
        except asyncio.CancelledError:
            logger.info(f"Таймер {timer_id} был отменен")
            try:
                await event.edit(f"{config.WARNING_EMOJI} Таймер отменен")
            except (ConnectionError, asyncio.CancelledError):
                # Не логируем отмену при выключении бота
                pass
        except Exception as e:
            logger.error(f"Ошибка в таймере {timer_id}: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка в таймере!")
    
    async def handle_countdown(self, event):
        """Обработка команды /countdown (простой отсчет без редактирования)"""
        try:
            seconds = int(event.pattern_match.group(1))
            
            if seconds > config.MAX_TIMER_SECONDS.total_seconds():
                max_hours = int(config.MAX_TIMER_SECONDS.total_seconds() // 3600)
                await event.edit(f"{config.ERROR_EMOJI} Максимальное время: {max_hours} часов")
                return

            # Создаем уникальный ID для отсчета
            timer_id = f"countdown_{event.chat_id}_{event.id}_{datetime.now().timestamp()}"

            # Запускаем отсчет как задачу
            task = asyncio.create_task(self._run_countdown(event, seconds, timer_id))
            self.active_timers[timer_id] = task
            self.bot.storage.increment_timers_created()

            await event.edit(f"{config.TIMER_EMOJI} Запускаю обратный отсчет с {seconds}. Можно отменить через /cancel.")

        except ValueError:
            await event.edit(f"{config.ERROR_EMOJI} Неверное число секунд!")
        except Exception as e:
            logger.error(f"Ошибка в countdown: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка в обратном отсчете!")

    async def _run_countdown(self, event, seconds: int, timer_id: str):
        """Выполняет обратный отсчет в фоновом режиме"""
        try:
            for i in range(seconds, 0, -1):
                # Отправляем новое сообщение вместо редактирования
                await event.reply(f"{config.TIMER_EMOJI} {i}")
                await asyncio.sleep(1)
            
            await event.reply(f"{config.SUCCESS_EMOJI} {config.DEFAULT_TIMER_END_TEXT}")

        except asyncio.CancelledError:
            logger.info(f"Отсчет {timer_id} был отменен")
            await event.edit(f"{config.WARNING_EMOJI} Обратный отсчет отменен.")
        
        except Exception as e:
            logger.error(f"Ошибка в выполнении отсчета {timer_id}: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка в обратном отсчете!")
        
        finally:
            # Удаляем таймер из активных в любом случае
            if timer_id in self.active_timers:
                del self.active_timers[timer_id]
    
    async def cancel_timer_by_id(self, timer_id: str) -> bool:
        """Отменяет конкретный таймер по ID
        
        Args:
            timer_id: ID таймера для отмены
            
        Returns:
            bool: True если таймер был найден и отменен, иначе False
        """
        if timer_id in self.active_timers:
            task = self.active_timers[timer_id]
            task.cancel()
            del self.active_timers[timer_id]
            self.bot.storage.remove_timer(timer_id)
            logger.info(f"Таймер {timer_id} был отменен по запросу")
            return True
        return False
        
    async def cancel_timers(self) -> int:
        """Отменяет все активные таймеры"""
        cancelled_count = 0
        
        for timer_id, task in list(self.active_timers.items()):
            task.cancel()
            cancelled_count += 1
        
        self.active_timers.clear()
        self.bot.storage.clear_timers()
        
        return cancelled_count
    
    async def get_active_timers(self) -> List[dict]:
        """Возвращает список активных таймеров"""
        timers = []
        
        for timer_id in self.active_timers.keys():
            timer_data = self.bot.storage.get_timer(timer_id)
            if timer_data:
                timers.append(timer_data)
        
        return timers
    
    async def restore_timers(self):
        """Восстанавливает таймеры после перезапуска бота"""
        try:
            all_timers = self.bot.storage.get_all_timers()
            
            for timer_data in all_timers:
                # Проверяем, не истек ли таймер
                start_time = datetime.fromisoformat(timer_data['start_time'])
                elapsed = (datetime.now() - start_time).total_seconds()
                remaining = timer_data['duration'] - elapsed
                
                timer_id = timer_data.get('id')
                if not timer_id:
                    continue

                if remaining <= 0:
                    # Таймер уже должен был закончиться
                    self.bot.storage.remove_timer(timer_id)
                    continue
                
                # Восстанавливаем таймер с оставшимся временем
                try:
                    chat_id = timer_data['chat_id']
                    message_id = timer_data['message_id']
                    spam_count = timer_data.get('spam_count', 1)
                    
                    # Получаем сообщение
                    message = await self.bot.client.get_messages(chat_id, ids=message_id)
                    if message:
                        # Создаем задачу для оставшегося времени
                        task = asyncio.create_task(
                            self._run_timer(message, int(remaining), spam_count, timer_id)
                        )
                        self.active_timers[timer_id] = task
                        
                        logger.info(f"Восстановлен таймер {timer_id} с {remaining:.0f} секунд")
                
                except Exception as e:
                    logger.error(f"Ошибка восстановления таймера {timer_id}: {e}")
                    self.bot.storage.remove_timer(timer_id)
        
        except Exception as e:
            logger.error(f"Ошибка при восстановлении таймеров: {e}")