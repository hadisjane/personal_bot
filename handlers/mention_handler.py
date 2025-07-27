#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from telethon import TelegramClient
from telethon.tl.types import Message

from utils.json_storage import JsonStorage
from utils.time_parser import TimeParser
from config import config

logger = logging.getLogger(__name__)

class MentionHandler:
    def __init__(self, bot):
        self.bot = bot
        self.active_mentions: Dict[str, asyncio.Task] = {}
        self.active_spam: Dict[str, asyncio.Task] = {}
    
    async def handle_mention(self, event):
        """Обработка команды /mention"""
        try:
            args = event.pattern_match.group(1).strip().split()
            if len(args) < 2:
                await event.edit(f"{config.ERROR_EMOJI} Используйте: /mention @username 30 [интервал]")
                return
            
            # Парсим username
            username = args[0]
            if not username.startswith('@'):
                await event.edit(f"{config.ERROR_EMOJI} Username должен начинаться с @")
                return
            
            # Парсим количество упоминаний
            try:
                mention_count = int(args[1])
                if mention_count <= 0:
                    await event.edit(f"{config.ERROR_EMOJI} Количество упоминаний должно быть больше 0")
                    return
                if mention_count > config.MAX_MENTION_COUNT:
                    mention_count = config.MAX_MENTION_COUNT
                    await event.edit(f"{config.WARNING_EMOJI} Максимальное количество упоминаний: {config.MAX_MENTION_COUNT}")
                    await asyncio.sleep(1)
            except ValueError:
                await event.edit(f"{config.ERROR_EMOJI} Неверное количество упоминаний!")
                return
            
            # Парсим интервал (опционально)
            interval = config.DEFAULT_MENTION_INTERVAL
            if len(args) > 2:
                interval_parsed = self.bot.time_parser.parse_interval(args[2])
                if interval_parsed is None:
                    await event.edit(f"{config.ERROR_EMOJI} Неверный формат интервала! Используйте: 1s, 500ms")
                    return
                interval = max(0.1, interval_parsed)  # Минимум 100ms
            
            # Создаем уникальный ID для упоминания
            mention_id = f"mention_{event.chat_id}_{event.id}_{datetime.now().timestamp()}"
            
            # Сохраняем информацию об упоминании
            mention_data = {
                'id': mention_id,
                'chat_id': event.chat_id,
                'message_id': event.id,
                'username': username,
                'count': mention_count,
                'interval': interval,
                'start_time': datetime.now().isoformat(),
                'type': 'mention'
            }
            
            self.bot.storage.save_mention(mention_data)
            self.bot.storage.increment_mentions_created()
            self.bot.storage.increment_command_usage('mention')
            
            # Запускаем упоминания
            task = asyncio.create_task(self._run_mentions(event, username, mention_count, interval, mention_id))
            self.active_mentions[mention_id] = task
            
            await event.edit(f"{config.MENTION_EMOJI} Начинаю упоминать {username} {mention_count} раз с интервалом {interval}с")
            
            logger.info(f"Запущены упоминания {username} {mention_count} раз с интервалом {interval}с")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_mention: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при создании упоминаний!")
    
    async def _run_mentions(self, event, username: str, count: int, interval: float, mention_id: str):
        """Запуск упоминаний"""
        try:
            for i in range(count):
                # Проверяем, не отменили ли задачу
                if mention_id not in self.active_mentions:
                    break
                
                await event.reply(f"{config.MENTION_EMOJI} {username}")
                
                # Задержка между упоминаниями (кроме последнего)
                if i < count - 1:
                    await asyncio.sleep(interval)
            
            # Обновляем исходное сообщение
            try:
                await event.edit(f"{config.SUCCESS_EMOJI} Упоминания {username} завершены ({count} раз)")
            except:
                pass
            
            # Удаляем упоминание из активных
            if mention_id in self.active_mentions:
                del self.active_mentions[mention_id]
            
            self.bot.storage.remove_mention(mention_id)
            
            logger.info(f"Упоминания {mention_id} завершены успешно")
            
        except asyncio.CancelledError:
            logger.info(f"Упоминания {mention_id} были отменены")
            try:
                await event.edit(f"{config.WARNING_EMOJI} Упоминания отменены")
            except:
                pass
            if mention_id in self.active_mentions:
                del self.active_mentions[mention_id]
            self.bot.storage.remove_mention(mention_id)
        except Exception as e:
            logger.error(f"Ошибка в упоминаниях {mention_id}: {e}")
            try:
                await event.edit(f"{config.ERROR_EMOJI} Ошибка в упоминаниях!")
            except:
                pass
    
    async def handle_spam(self, event):
        """Обработка команды /spam"""
        try:
            full_text = event.pattern_match.group(1).strip()
            
            # Поддерживаемые форматы:
            # /spam "текст" 10
            # /spam @username "текст" 10  
            # /spam текст_без_пробелов 5
            
            # Пытаемся определить формат команды
            parts = self._parse_spam_command(full_text)
            
            if not parts:
                await event.edit(f"{config.ERROR_EMOJI} Используйте: /spam \"текст\" 10 или /spam @username \"текст\" 10")
                return
            
            target_user, spam_text, spam_count = parts
            
            # Проверяем ограничения
            if spam_count > config.MAX_SPAM_COUNT:
                spam_count = config.MAX_SPAM_COUNT
                await event.edit(f"{config.WARNING_EMOJI} Максимальное количество сообщений: {config.MAX_SPAM_COUNT}")
                await asyncio.sleep(1)
            
            # Создаем уникальный ID для спама
            spam_id = f"spam_{event.chat_id}_{event.id}_{datetime.now().timestamp()}"
            
            # Сохраняем информацию о спаме
            spam_data = {
                'id': spam_id,
                'chat_id': event.chat_id,
                'message_id': event.id,
                'target_user': target_user,
                'text': spam_text,
                'count': spam_count,
                'start_time': datetime.now().isoformat(),
                'type': 'spam'
            }
            
            self.bot.storage.save_mention(spam_data)
            self.bot.storage.increment_command_usage('spam')
            
            # Запускаем спам
            task = asyncio.create_task(self._run_spam(event, target_user, spam_text, spam_count, spam_id))
            self.active_spam[spam_id] = task
            
            target_str = f"пользователю {target_user}" if target_user else "в чат"
            await event.edit(f"💬 Начинаю спам {target_str}: \"{spam_text}\" ({spam_count} раз)")
            
            logger.info(f"Запущен спам: {spam_text} {spam_count} раз")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_spam: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при создании спама!")
    
    def _parse_spam_command(self, text: str) -> Optional[tuple]:
        """Парсит команду спама"""
        try:
            # Паттерн 1: /spam @username "текст" 10
            pattern1 = re.match(r'^(@\w+)\s+"([^"]+)"\s+(\d+)$', text)
            if pattern1:
                return pattern1.group(1), pattern1.group(2), int(pattern1.group(3))
            
            # Паттерн 2: /spam @username 'текст' 10  
            pattern2 = re.match(r"^(@\w+)\s+'([^']+)'\s+(\d+)$", text)
            if pattern2:
                return pattern2.group(1), pattern2.group(2), int(pattern2.group(3))
            
            # Паттерн 3: /spam "текст" 10
            pattern3 = re.match(r'^"([^"]+)"\s+(\d+)$', text)
            if pattern3:
                return None, pattern3.group(1), int(pattern3.group(2))
            
            # Паттерн 4: /spam 'текст' 10
            pattern4 = re.match(r"^'([^']+)'\s+(\d+)$", text)
            if pattern4:
                return None, pattern4.group(1), int(pattern4.group(2))
            
            # Паттерн 5: /spam текст_без_пробелов 10
            pattern5 = re.match(r'^(\S+)\s+(\d+)$', text)
            if pattern5 and not pattern5.group(1).startswith('@'):
                return None, pattern5.group(1), int(pattern5.group(2))
            
            # Паттерн 6: /spam @username текст_без_пробелов 10
            pattern6 = re.match(r'^(@\w+)\s+(\S+)\s+(\d+)$', text)
            if pattern6:
                return pattern6.group(1), pattern6.group(2), int(pattern6.group(3))
            
            return None
            
        except (ValueError, AttributeError):
            return None
    
    async def _run_spam(self, event, target_user: Optional[str], text: str, count: int, spam_id: str):
        """Запуск спама"""
        try:
            for i in range(count):
                # Проверяем, не отменили ли задачу
                if spam_id not in self.active_spam:
                    break
                
                # Формируем сообщение
                if target_user:
                    message = f"{target_user} {text}"
                else:
                    message = text
                
                await event.reply(message)
                
                # Задержка между сообщениями (кроме последнего)
                if i < count - 1:
                    await asyncio.sleep(0.2)  # 200ms между сообщениями
            
            # Обновляем исходное сообщение
            try:
                target_str = f"пользователю {target_user}" if target_user else "в чат"
                await event.edit(f"{config.SUCCESS_EMOJI} Спам {target_str} завершен ({count} сообщений)")
            except:
                pass
            
            # Удаляем спам из активных
            if spam_id in self.active_spam:
                del self.active_spam[spam_id]
            
            self.bot.storage.remove_mention(spam_id)
            
            logger.info(f"Спам {spam_id} завершен успешно")
            
        except asyncio.CancelledError:
            logger.info(f"Спам {spam_id} был отменен")
            try:
                await event.edit(f"{config.WARNING_EMOJI} Спам отменен")
            except:
                pass
            if spam_id in self.active_spam:
                del self.active_spam[spam_id]
            self.bot.storage.remove_mention(spam_id)
        except Exception as e:
            logger.error(f"Ошибка в спаме {spam_id}: {e}")
            try:
                await event.edit(f"{config.ERROR_EMOJI} Ошибка в спаме!")
            except:
                pass
    
    async def cancel_mention_by_id(self, mention_id: str) -> bool:
        """Отменяет конкретное упоминание или спам по ID
        
        Args:
            mention_id: ID упоминания/спама для отмены
            
        Returns:
            bool: True если упоминание/спам был найден и отменен, иначе False
        """
        # Проверяем в обычных упоминаниях
        if mention_id in self.active_mentions:
            task = self.active_mentions[mention_id]
            task.cancel()
            del self.active_mentions[mention_id]
            self.bot.storage.remove_mention(mention_id)
            logger.info(f"Упоминание {mention_id} было отменено по запросу")
            return True
            
        # Проверяем в спаме
        if mention_id in self.active_spam:
            task = self.active_spam[mention_id]
            task.cancel()
            del self.active_spam[mention_id]
            self.bot.storage.remove_mention(mention_id)
            logger.info(f"Спам {mention_id} был отменен по запросу")
            return True
            
        return False
    
    async def cancel_mentions(self) -> int:
        """Отменяет все активные упоминания"""
        cancelled_count = 0
        
        # Отменяем упоминания
        for mention_id, task in list(self.active_mentions.items()):
            task.cancel()
            cancelled_count += 1
        
        # Отменяем спам
        for spam_id, task in list(self.active_spam.items()):
            task.cancel()
            cancelled_count += 1
        
        self.active_mentions.clear()
        self.active_spam.clear()
        self.bot.storage.clear_mentions()
        
        return cancelled_count
    
    async def get_active_mentions(self) -> List[dict]:
        """Возвращает список активных упоминаний и спама"""
        mentions = []
        
        # Активные упоминания
        for mention_id in self.active_mentions.keys():
            mention_data = self.bot.storage.get_mention(mention_id)
            if mention_data:
                mentions.append(mention_data)
        
        # Активный спам
        for spam_id in self.active_spam.keys():
            spam_data = self.bot.storage.get_mention(spam_id)
            if spam_data:
                mentions.append(spam_data)
        
        return mentions
    
    async def restore_mentions(self):
        """Восстанавливает упоминания после перезапуска бота"""
        try:
            saved_mentions = self.bot.storage.get_all_mentions()
            
            for mention_data in saved_mentions:
                # Для упоминаний и спама не восстанавливаем состояние
                # так как они должны выполняться быстро
                # Просто удаляем из хранилища
                mention_id = mention_data.get('id')
                if mention_id:
                    self.bot.storage.remove_mention(mention_id)
                    logger.info(f"Удалено неактивное упоминание/спам {mention_id}")
        
        except Exception as e:
            logger.error(f"Ошибка при восстановлении упоминаний: {e}")