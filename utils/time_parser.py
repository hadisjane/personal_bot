import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Union

class TimeParser:
    """A utility class for parsing time expressions and calculating time differences."""
    
    def __init__(self):
        # Regular expressions for different time units
        self.time_patterns = {
            'seconds': r'(\d+)\s*(сек|с|sec|s)',
            'minutes': r'(\d+)\s*(мин|м|min|m)',
            'hours': r'(\d+)\s*(час|ч|h|hr|hour|часа|часов|часам|часах|часы)',
            'days': r'(\d+)\s*(день|дня|дней|дню|днём|дне|дни|d|day|days)',
            'weeks': r'(\d+)\s*(недел[ьяи]|неделю|неделей|неделе|неделям|неделях|недели|w|week|weeks)',
            'months': r'(\d+)\s*(месяц|месяца|месяцев|месяцу|месяцем|месяце|месяцы|мес|mth|month|months)',
            'years': r'(\d+)\s*(год|года|лет|году|годом|годе|годы|y|year|years)',
        }
    
    def parse_duration(self, text: str) -> Optional[timedelta]:
        """Parse a duration string into a timedelta object.
        
        Args:
            text: The duration string to parse (e.g., '2 hours 30 minutes').
            
        Returns:
            A timedelta object representing the duration, or None if parsing fails.
        """
        total_seconds = 0
        found = False
        
        for unit, pattern in self.time_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = int(match.group(1))
                found = True
                
                if unit == 'seconds':
                    total_seconds += value
                elif unit == 'minutes':
                    total_seconds += value * 60
                elif unit == 'hours':
                    total_seconds += value * 3600
                elif unit == 'days':
                    total_seconds += value * 86400
                elif unit == 'weeks':
                    total_seconds += value * 604800
                elif unit == 'months':
                    total_seconds += value * 2592000  # Approximate 30 days
                elif unit == 'years':
                    total_seconds += value * 31536000  # Approximate 365 days
        
        return timedelta(seconds=total_seconds) if found else None
    
    def parse_datetime(self, text: str) -> Optional[datetime]:
        """Parse a datetime string into a datetime object.
        
        Args:
            text: The datetime string to parse (e.g., '2023-12-31 23:59').
            
        Returns:
            A datetime object representing the parsed time, or None if parsing fails.
        """
        try:
            # Try common datetime formats
            formats = [
                '%Y-%m-%d %H:%M',    # 2023-12-31 23:59
                '%d.%m.%Y %H:%M',    # 31.12.2023 23:59
                '%H:%M',              # 23:59 (today's date)
                '%Y-%m-%d',          # 2023-12-31
                '%d.%m.%Y',          # 31.12.2023
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(text, fmt)
                    # If only time was provided, use today's date
                    if fmt == '%H:%M':
                        now = datetime.now()
                        dt = dt.replace(year=now.year, month=now.month, day=now.day)
                    # If only date was provided, use current time
                    elif fmt in ['%Y-%m-%d', '%d.%m.%Y']:
                        now = datetime.now()
                        dt = dt.replace(hour=now.hour, minute=now.minute, second=0, microsecond=0)
                    return dt
                except ValueError:
                    continue
        except Exception as e:
            logger.error(f"Error parsing datetime: {e}")
        
        return None
    
    def time_until(self, target_time: datetime) -> timedelta:
        """Calculate the time difference between now and the target time.
        
        Args:
            target_time: The target datetime to calculate the difference to.
            
        Returns:
            A timedelta representing the time until the target time.
        """
        now = datetime.now()
        return target_time - now if target_time > now else timedelta(0)
    
    def format_duration(self, delta: timedelta) -> str:
        """Format a timedelta into a human-readable string.
        
        Args:
            delta: The timedelta to format.
            
        Returns:
            A human-readable string representation of the duration.
        """
        if not delta:
            return "0 секунд"
            
        total_seconds = int(delta.total_seconds())
        if total_seconds < 0:
            return "0 секунд"
            
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        
        parts = []
        if days > 0:
            parts.append(f"{days} {self._plural_days(days)}")
        if hours > 0:
            parts.append(f"{hours} {self._plural_hours(hours)}")
        if minutes > 0:
            parts.append(f"{minutes} {self._plural_minutes(minutes)}")
        if seconds > 0 or not parts:
            parts.append(f"{seconds} {self._plural_seconds(seconds)}")
            
        return " ".join(parts)
    
    def seconds_to_string(self, seconds: int) -> str:
        """Formats seconds into a compact, human-readable string."""
        if seconds < 0:
            seconds = 0
        
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, secs = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{int(days)}д")
        if hours > 0:
            parts.append(f"{int(hours)}ч")
        if minutes > 0:
            parts.append(f"{int(minutes)}м")
        if secs > 0 or not parts:
            parts.append(f"{int(secs)}с")
            
        return " ".join(parts)

    def _plural_days(self, n: int) -> str:
        """Return the correct plural form for days."""
        if n % 10 == 1 and n % 100 != 11:
            return "день"
        elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
            return "дня"
        else:
            return "дней"
    
    def _plural_hours(self, n: int) -> str:
        """Return the correct plural form for hours."""
        if n % 10 == 1 and n % 100 != 11:
            return "час"
        elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
            return "часа"
        else:
            return "часов"
    
    def _plural_minutes(self, n: int) -> str:
        """Return the correct plural form for minutes."""
        if n % 10 == 1 and n % 100 != 11:
            return "минута"
        elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
            return "минуты"
        else:
            return "минут"
    
    def _plural_seconds(self, n: int) -> str:
        """Return the correct plural form for seconds."""
        if n % 10 == 1 and n % 100 != 11:
            return "секунда"
        elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
            return "секунды"
        else:
            return "секунд"
