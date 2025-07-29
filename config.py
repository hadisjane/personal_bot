#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Optional
from datetime import timedelta

class Config:
    """Конфигурация бота"""
    
    def __init__(self):
        # Telegram API настройки
        self.API_ID: int = int(os.getenv('API_ID', '0'))
        self.API_HASH: str = os.getenv('API_HASH', '')
        self.PHONE_NUMBER: str = os.getenv('PHONE_NUMBER', '')
        self.BOT_OWNER_ID: int = int(os.getenv('BOT_OWNER_ID', '0'))
        
        # Ограничения безопасности
        self.MAX_TIMER_SECONDS: timedelta = timedelta(days=1)  # 24 часа
        self.MAX_SPAM_COUNT: int = 1000  # Максимум сообщений для спама
        self.MAX_MENTION_COUNT: int = 100  # Максимум упоминаний
        self.MIN_COMMAND_COOLDOWN: float = 0.5  # Кулдаун между командами (секунды)
        
        # Пути к файлам данных
        self.DATA_DIR: str = 'data'
        self.TIMERS_FILE: str = os.path.join(self.DATA_DIR, 'timers.json')
        self.WAKE_ALARMS_FILE: str = os.path.join(self.DATA_DIR, 'wake_alarms.json')  
        self.MENTIONS_FILE: str = os.path.join(self.DATA_DIR, 'mentions.json')
        self.REMINDERS_FILE: str = os.path.join(self.DATA_DIR, 'reminders.json')
        self.STATS_FILE: str = os.path.join(self.DATA_DIR, 'stats.json')
        
        # Пути к ресурсам
        self.ASSETS_DIR: str = 'assets'
        self.QUOTES_FILE: str = os.path.join(self.ASSETS_DIR, 'quotes.json')
        self.JOKES_FILE: str = os.path.join(self.ASSETS_DIR, 'jokes.json')
        self.ASCII_ART_FILE: str = os.path.join(self.ASSETS_DIR, 'ascii_art.json')
        self.INTERACTIONS_FILE: str = os.path.join(self.ASSETS_DIR, 'interactions.json')
        
        # Настройки по умолчанию
        self.DEFAULT_WAKE_MESSAGES: int = 10  # Количество сообщений будильника
        self.DEFAULT_TIMER_SPAM: int = 1  # Количество сообщений окончания таймера
        self.DEFAULT_MENTION_INTERVAL: float = 0.5  # Интервал между упоминаниями (секунды)
        
        # Тексты по умолчанию
        self.DEFAULT_WAKE_TEXT: str = "🔔 ВСТАВАЙ!!!"
        self.DEFAULT_TIMER_END_TEXT: str = "⏰ ВРЕМЯ ВЫШЛО!"
        self.DEFAULT_REMINDER_TEXT: str = "💭 Напоминание:"
        
        # Эмодзи и форматирование
        self.TIMER_EMOJI: str = "⏰"
        self.WAKE_EMOJI: str = "🔔"
        self.MENTION_EMOJI: str = "👤"
        self.SUCCESS_EMOJI: str = "✅"
        self.ERROR_EMOJI: str = "❌"
        self.WARNING_EMOJI: str = "⚠️"
        self.INFO_EMOJI: str = "ℹ️"
        
        # Создаем необходимые директории
        self._create_directories()
        
        # Валидация конфигурации
        self._validate_config()
    
    def _create_directories(self):
        """Создает необходимые директории если их нет"""
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.ASSETS_DIR, exist_ok=True)
    
    def _validate_config(self):
        """Проверяет корректность конфигурации"""
        if not self.API_ID or not self.API_HASH:
            raise ValueError("API_ID и API_HASH должны быть установлены")
        
        if not self.PHONE_NUMBER:
            raise ValueError("PHONE_NUMBER должен быть установлен")
            
        if not self.BOT_OWNER_ID:
            raise ValueError("BOT_OWNER_ID должен быть установлен")
    
    def get_user_setting(self, user_id: int, setting: str, default=None):
        """Получает пользовательскую настройку (заглушка для будущего расширения)"""
        # В будущем можно добавить персональные настройки для каждого пользователя
        return default
    
    def set_user_setting(self, user_id: int, setting: str, value):
        """Устанавливает пользовательскую настройку (заглушка для будущего расширения)"""
        # В будущем можно добавить персональные настройки для каждого пользователя
        pass

# Создаем глобальный экземпляр конфигурации
config = Config()