#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from typing import Optional

class TimeParser:
    """Парсер времени для команд бота"""
    
    def __init__(self):
        # Регулярное выражение для парсинга времени
        self.time_pattern = re.compile(r'^(\d+)([smhd])$', re.IGNORECASE)
        
        # Множители для перевода в секунды
        self.multipliers = {
            's': 1,      # секунды
            'm': 60,     # минуты  
            'h': 3600,   # часы
            'd': 86400   # дни
        }
    
    def parse_time(self, time_str: str) -> Optional[int]:
        """
        Парсит строку времени и возвращает количество секунд
        
        Поддерживаемые форматы:
        - 30s - 30 секунд
        - 5m - 5 минут
        - 2h - 2 часа  
        - 1d - 1 день
        
        Args:
            time_str: Строка времени (например, "30s", "5m")
            
        Returns:
            Количество секунд или None если формат неверный
        """
        if not time_str:
            return None
            
        match = self.time_pattern.match(time_str.strip())
        if not match:
            return None
        
        try:
            number = int(match.group(1))
            unit = match.group(2).lower()
            
            if unit not in self.multipliers:
                return None
            
            if number <= 0:
                return None
                
            return number * self.multipliers[unit]
            
        except (ValueError, AttributeError):
            return None
    
    def seconds_to_string(self, seconds: int) -> str:
        """
        Преобразует секунды в читаемую строку
        
        Args:
            seconds: Количество секунд
            
        Returns:
            Строка вида "1ч 30м 45с"
        """
        if seconds <= 0:
            return "0с"
        
        parts = []
        
        # Дни
        if seconds >= 86400:
            days = seconds // 86400
            parts.append(f"{days}д")
            seconds %= 86400
        
        # Часы
        if seconds >= 3600:
            hours = seconds // 3600
            parts.append(f"{hours}ч")
            seconds %= 3600
        
        # Минуты
        if seconds >= 60:
            minutes = seconds // 60
            parts.append(f"{minutes}м")
            seconds %= 60
        
        # Секунды
        if seconds > 0:
            parts.append(f"{seconds}с")
        
        return " ".join(parts)
    
    def validate_time_range(self, seconds: int, min_seconds: int = 1, max_seconds: int = 86400) -> bool:
        """
        Проверяет, находится ли время в допустимом диапазоне
        
        Args:
            seconds: Количество секунд для проверки
            min_seconds: Минимальное количество секунд (по умолчанию 1)
            max_seconds: Максимальное количество секунд (по умолчанию 24 часа)
            
        Returns:
            True если время в допустимом диапазоне
        """
        return min_seconds <= seconds <= max_seconds
    
    def parse_interval(self, interval_str: str) -> Optional[float]:
        """
        Парсит интервал для команд с повторением
        
        Поддерживаемые форматы:
        - 1s, 2s - секунды (возвращает float)
        - 500ms - миллисекунды  
        
        Args:
            interval_str: Строка интервала
            
        Returns:
            Интервал в секундах (float) или None
        """
        if not interval_str:
            return None
        
        # Миллисекунды
        ms_pattern = re.compile(r'^(\d+)ms$', re.IGNORECASE)
        ms_match = ms_pattern.match(interval_str.strip())
        if ms_match:
            try:
                ms = int(ms_match.group(1))
                return ms / 1000.0
            except ValueError:
                return None
        
        # Секунды (поддерживаем дробные)
        s_pattern = re.compile(r'^(\d+(?:\.\d+)?)s$', re.IGNORECASE)
        s_match = s_pattern.match(interval_str.strip())
        if s_match:
            try:
                return float(s_match.group(1))
            except ValueError:
                return None
        
        return None
    
    def format_duration(self, start_time, end_time = None) -> str:
        """
        Форматирует продолжительность между двумя временными метками
        
        Args:
            start_time: Время начала (datetime)
            end_time: Время окончания (datetime), если None - используется текущее время
            
        Returns:
            Отформатированная строка продолжительности
        """
        from datetime import datetime
        
        if end_time is None:
            end_time = datetime.now()
        
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        
        return self.seconds_to_string(total_seconds)
    
    def get_time_units_help(self) -> str:
        """Возвращает справку по единицам времени"""
        return """
📖 **Единицы времени:**
• `s` - секунды (например: 30s)
• `m` - минуты (например: 5m) 
• `h` - часы (например: 2h)
• `d` - дни (например: 1d)

📝 **Примеры:**
• `/timer 30s` - таймер на 30 секунд
• `/wake 5m` - будильник через 5 минут
• `/remind 2h "встреча"` - напоминание через 2 часа
        """.strip()