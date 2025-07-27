#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import config

logger = logging.getLogger(__name__)

class JsonStorage:
    """Класс для работы с JSON хранилищем данных"""
    
    def __init__(self):
        self._lock = asyncio.Lock()
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Создает файлы данных если их нет"""
        files_to_create = [
            config.TIMERS_FILE,
            config.WAKE_ALARMS_FILE,
            config.MENTIONS_FILE,
            config.REMINDERS_FILE,
            config.STATS_FILE
        ]
        
        for file_path in files_to_create:
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=2)
                    logger.info(f"Создан файл данных: {file_path}")
                except Exception as e:
                    logger.error(f"Ошибка создания файла {file_path}: {e}")
    
    async def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Загружает данные из JSON файла"""
        async with self._lock:
            try:
                if not os.path.exists(file_path):
                    return {}
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
                    
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Ошибка загрузки {file_path}: {e}")
                return {}
            except Exception as e:
                logger.error(f"Критическая ошибка загрузки {file_path}: {e}")
                return {}
    
    async def _save_json(self, file_path: str, data: Dict[str, Any]):
        """Сохраняет данные в JSON файл"""
        async with self._lock:
            try:
                # Создаем временный файл для атомарного сохранения
                temp_file = f"{file_path}.tmp"
                
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
                # Атомарно заменяем основной файл
                os.replace(temp_file, file_path)
                
            except Exception as e:
                logger.error(f"Ошибка сохранения {file_path}: {e}")
                # Удаляем временный файл если он остался
                if os.path.exists(f"{file_path}.tmp"):
                    try:
                        os.remove(f"{file_path}.tmp")
                    except:
                        pass
    
    # === ТАЙМЕРЫ ===
    
    async def save_timer(self, timer_id: str, timer_data: Dict[str, Any]):
        """Сохраняет данные таймера"""
        timers = await self._load_json(config.TIMERS_FILE)
        timers[timer_id] = timer_data
        await self._save_json(config.TIMERS_FILE, timers)
    
    async def get_timer(self, timer_id: str) -> Optional[Dict[str, Any]]:
        """Получает данные таймера"""
        timers = await self._load_json(config.TIMERS_FILE)
        return timers.get(timer_id)
    
    async def remove_timer(self, timer_id: str):
        """Удаляет таймер"""
        timers = await self._load_json(config.TIMERS_FILE)
        if timer_id in timers:
            del timers[timer_id]
            await self._save_json(config.TIMERS_FILE, timers)
    
    async def get_all_timers(self) -> Dict[str, Any]:
        """Получает все таймеры"""
        return await self._load_json(config.TIMERS_FILE)
    
    async def clear_timers(self):
        """Очищает все таймеры"""
        await self._save_json(config.TIMERS_FILE, {})
    
    # === БУДИЛЬНИКИ ===
    
    async def save_alarm(self, alarm_id: str, alarm_data: Dict[str, Any]):
        """Сохраняет данные будильника"""
        alarms = await self._load_json(config.WAKE_ALARMS_FILE)
        alarms[alarm_id] = alarm_data
        await self._save_json(config.WAKE_ALARMS_FILE, alarms)
    
    async def get_alarm(self, alarm_id: str) -> Optional[Dict[str, Any]]:
        """Получает данные будильника"""
        alarms = await self._load_json(config.WAKE_ALARMS_FILE)
        return alarms.get(alarm_id)
    
    async def remove_alarm(self, alarm_id: str):
        """Удаляет будильник"""
        alarms = await self._load_json(config.WAKE_ALARMS_FILE)
        if alarm_id in alarms:
            del alarms[alarm_id]
            await self._save_json(config.WAKE_ALARMS_FILE, alarms)
    
    async def get_all_alarms(self) -> Dict[str, Any]:
        """Получает все будильники"""
        return await self._load_json(config.WAKE_ALARMS_FILE)
    
    async def clear_alarms(self):
        """Очищает все будильники"""
        await self._save_json(config.WAKE_ALARMS_FILE, {})
    
    # === УПОМИНАНИЯ ===
    
    async def save_mention(self, mention_id: str, mention_data: Dict[str, Any]):
        """Сохраняет данные упоминания"""
        mentions = await self._load_json(config.MENTIONS_FILE)
        mentions[mention_id] = mention_data
        await self._save_json(config.MENTIONS_FILE, mentions)
    
    async def get_mention(self, mention_id: str) -> Optional[Dict[str, Any]]:
        """Получает данные упоминания"""
        mentions = await self._load_json(config.MENTIONS_FILE)
        return mentions.get(mention_id)
    
    async def remove_mention(self, mention_id: str):
        """Удаляет упоминание"""
        mentions = await self._load_json(config.MENTIONS_FILE)
        if mention_id in mentions:
            del mentions[mention_id]
            await self._save_json(config.MENTIONS_FILE, mentions)
    
    async def get_all_mentions(self) -> Dict[str, Any]:
        """Получает все упоминания"""
        return await self._load_json(config.MENTIONS_FILE)
    
    async def clear_mentions(self):
        """Очищает все упоминания"""
        await self._save_json(config.MENTIONS_FILE, {})
    
    # === НАПОМИНАНИЯ ===
    
    async def save_reminder(self, reminder_id: str, reminder_data: Dict[str, Any]):
        """Сохраняет данные напоминания"""
        reminders = await self._load_json(config.REMINDERS_FILE)
        reminders[reminder_id] = reminder_data
        await self._save_json(config.REMINDERS_FILE, reminders)
    
    async def get_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        """Получает данные напоминания"""
        reminders = await self._load_json(config.REMINDERS_FILE)
        return reminders.get(reminder_id)
    
    async def remove_reminder(self, reminder_id: str):
        """Удаляет напоминание"""
        reminders = await self._load_json(config.REMINDERS_FILE)
        if reminder_id in reminders:
            del reminders[reminder_id]
            await self._save_json(config.REMINDERS_FILE, reminders)
    
    async def get_all_reminders(self) -> Dict[str, Any]:
        """Получает все напоминания"""
        return await self._load_json(config.REMINDERS_FILE)
    
    async def clear_reminders(self):
        """Очищает все напоминания"""
        await self._save_json(config.REMINDERS_FILE, {})
    
    # === СТАТИСТИКА ===
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получает статистику"""
        stats = await self._load_json(config.STATS_FILE)
        
        # Инициализируем базовую структуру если нужно
        if not stats:
            stats = {
                'commands_used': {},
                'total_commands': 0,
                'start_time': datetime.now().isoformat(),
                'last_command_time': None,
                'timers_created': 0,
                'alarms_created': 0,
                'mentions_created': 0
            }
            await self._save_json(config.STATS_FILE, stats)
        
        return stats
    
    async def increment_command_usage(self, command: str):
        """Увеличивает счетчик использования команды"""
        stats = await self.get_stats()
        
        stats['commands_used'][command] = stats['commands_used'].get(command, 0) + 1
        stats['total_commands'] = stats.get('total_commands', 0) + 1
        stats['last_command_time'] = datetime.now().isoformat()
        
        await self._save_json(config.STATS_FILE, stats)
    
    async def increment_counter(self, counter_name: str):
        """Увеличивает указанный счетчик"""
        stats = await self.get_stats()
        stats[counter_name] = stats.get(counter_name, 0) + 1
        await self._save_json(config.STATS_FILE, stats)
    
    # === ОЧИСТКА ВСЕХ ДАННЫХ ===
    
    async def clear_all_data(self):
        """Очищает все данные (используется для полного сброса)"""
        await self.clear_timers()
        await self.clear_alarms()
        await self.clear_mentions()
        await self.clear_reminders()
        logger.info("Все данные очищены")
    
    # === РЕЗЕРВНОЕ КОПИРОВАНИЕ ===
    
    async def create_backup(self) -> str:
        """Создает резервную копию всех данных"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backup_{timestamp}"
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            files_to_backup = [
                config.TIMERS_FILE,
                config.WAKE_ALARMS_FILE,
                config.MENTIONS_FILE,
                config.REMINDERS_FILE,
                config.STATS_FILE
            ]
            
            for file_path in files_to_backup:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    backup_path = os.path.join(backup_dir, filename)
                    
                    data = await self._load_json(file_path)
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Создана резервная копия в {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return ""