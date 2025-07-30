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
        
        # Simple time pattern for short format (e.g., 30s, 5m, 2h, 1d)
        self.simple_time_pattern = re.compile(r'^(\d+)([smhd])$', re.IGNORECASE)
        
        # Multipliers for simple time format
        self.multipliers = {
            's': 1,      # seconds
            'm': 60,     # minutes
            'h': 3600,   # hours
            'd': 86400   # days
        }
    
    def parse_interval(self, interval_str: str) -> Optional[float]:
        """
        Parses an interval string into seconds (as float).
        
        Supported formats:
        - 1s, 2s - seconds (returns float)
        - 500ms - milliseconds
        
        Args:
            interval_str: The interval string to parse
            
        Returns:
            Interval in seconds (float) or None if parsing fails
        """
        if not interval_str:
            return None
        
        # Milliseconds
        ms_pattern = re.compile(r'^(\d+)ms$', re.IGNORECASE)
        ms_match = ms_pattern.match(interval_str.strip())
        if ms_match:
            try:
                ms = int(ms_match.group(1))
                return ms / 1000.0
            except ValueError:
                return None
        
        # Seconds (supports fractions)
        s_pattern = re.compile(r'^(\d+(?:\.\d+)?)s$', re.IGNORECASE)
        s_match = s_pattern.match(interval_str.strip())
        if s_match:
            try:
                return float(s_match.group(1))
            except ValueError:
                return None
        
        # Try simple time format (e.g., 30s, 5m)
        simple_seconds = self.parse_time(interval_str)
        if simple_seconds is not None:
            return float(simple_seconds)
        
        return None
    
    def parse_time(self, time_str: str) -> Optional[int]:
        """
        Parses a time string and returns the number of seconds.
        
        Supports formats:
        - 30s - 30 seconds
        - 5m - 5 minutes
        - 2h - 2 hours
        - 1d - 1 day
        
        Args:
            time_str: Time string (e.g., "30s", "5m")
            
        Returns:
            Number of seconds or None if format is invalid
        """
        if not time_str:
            return None
            
        # Try simple format first (e.g., 30s, 5m, 2h, 1d)
        match = self.simple_time_pattern.match(time_str.strip())
        if match:
            try:
                number = int(match.group(1))
                unit = match.group(2).lower()
                
                if unit in self.multipliers and number > 0:
                    return number * self.multipliers[unit]
            except (ValueError, AttributeError):
                pass  # Fall through to complex parsing
        
        # Fall back to complex parsing if simple format fails
        return self.parse_duration(time_str).total_seconds() if self.parse_duration(time_str) else None
    
    def parse_duration(self, text: str) -> Optional[timedelta]:
        """
        Parse a duration string into a timedelta object.
        
        Args:
            text: The duration string to parse (e.g., '2 hours 30 minutes').
            
        Returns:
            A timedelta object representing the duration, or None if parsing fails.
        """
        if not text:
            return None
            
        total_seconds = 0
        found = False
        
        for unit, pattern in self.time_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
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
                except (ValueError, IndexError):
                    continue
        
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
    
    def seconds_to_string(self, seconds: int) -> str:
        """
        Converts seconds to a human-readable string.
        
        Args:
            seconds: Number of seconds
            
        Returns:
            String in format like "1h 30m 45s"
        """
        if not isinstance(seconds, (int, float)) or seconds <= 0:
            return "0s"
        
        seconds = int(round(seconds))
        parts = []
        
        # Days
        if seconds >= 86400:
            days = seconds // 86400
            parts.append(f"{days}д")
            seconds %= 86400
        
        # Hours
        if seconds >= 3600 or parts:  # Show hours if we have days or hours > 0
            hours = seconds // 3600
            parts.append(f"{hours}ч")
            seconds %= 3600
        
        # Minutes
        if seconds >= 60 or parts:  # Show minutes if we have hours or minutes > 0
            minutes = seconds // 60
            parts.append(f"{minutes}м")
            seconds %= 60
        
        # Seconds (always show if no other parts, or if we have seconds)
        if not parts or seconds > 0:
            parts.append(f"{seconds}с")
        
        return " ".join(parts)
    
    def validate_time_range(self, seconds: int, min_seconds: int = 1, max_seconds: int = 86400) -> bool:
        """
        Validates if a time duration is within the allowed range.
        
        Args:
            seconds: Time in seconds to validate
            min_seconds: Minimum allowed seconds (default: 1)
            max_seconds: Maximum allowed seconds (default: 24 hours)
            
        Returns:
            True if the time is within the valid range
        """
        return min_seconds <= seconds <= max_seconds
    
    def format_duration(self, start_time, end_time=None) -> str:
        """
        Formats the duration between two timestamps.
        
        Args:
            start_time: Start time (datetime)
            end_time: End time (datetime), if None uses current time
            
        Returns:
            Formatted duration string
        """
        if not isinstance(start_time, datetime):
            return ""
            
        if end_time is None:
            end_time = datetime.now()
        
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        
        return self.seconds_to_string(total_seconds)
    
    def get_time_units_help(self) -> str:
        """Returns help text for time units"""
        return """
📖 **Time units:**
• `s` - seconds (e.g., 30s)
• `m` - minutes (e.g., 5m) 
• `h` - hours (e.g., 2h)
• `d` - days (e.g., 1d)

📝 **Examples:**
• `/timer 30s` - 30-second timer
• `/wake 5m` - alarm in 5 minutes
• `/remind 2h "meeting"` - reminder in 2 hours
        """.strip()
    
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
