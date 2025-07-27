import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

class JsonStorage:
    """A JSON-based storage system that manages multiple data files."""

    def __init__(self, data_dir: str = 'data'):
        """Initialize the storage manager.

        Args:
            data_dir: The directory where data files are stored.
        """
        self.data_dir = data_dir
        self.file_map = {
            'timers': 'timers.json',
            'alarms': 'wake_alarms.json',
            'reminders': 'reminders.json',
            'mentions': 'mentions.json',
            'stats': 'stats.json',
        }
        self.cache: Dict[str, Any] = {}
        os.makedirs(self.data_dir, exist_ok=True)

    def _get_path(self, key: str) -> str:
        """Get the full path for a data file."""
        filename = self.file_map.get(key)
        if not filename:
            raise ValueError(f"Unknown data key: {key}")
        return os.path.join(self.data_dir, filename)

    def _load(self, key: str) -> Any:
        """Load data from a specific JSON file."""
        if key in self.cache:
            return self.cache[key]

        file_path = self._get_path(key)
        if not os.path.exists(file_path):
            return [] if key != 'stats' else {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cache[key] = data
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            return [] if key != 'stats' else {}

    def _save(self, key: str, data: Any) -> None:
        """Save data to a specific JSON file."""
        self.cache[key] = data
        file_path = self._get_path(key)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    # Generic list-based methods
    def _get_all(self, key: str) -> List[Dict]:
        return self._load(key)

    def _get_one(self, key: str, item_id: str) -> Optional[Dict]:
        items = self._load(key)
        for item in items:
            if item.get('id') == item_id:
                return item
        return None

    def _save_one(self, key: str, item_data: Dict) -> None:
        items = self._load(key)
        # Remove existing item if it's an update
        items = [i for i in items if i.get('id') != item_data.get('id')]
        items.append(item_data)
        self._save(key, items)

    def _remove_one(self, key: str, item_id: str) -> bool:
        items = self._load(key)
        initial_count = len(items)
        items = [i for i in items if i.get('id') != item_id]
        if len(items) < initial_count:
            self._save(key, items)
            return True
        return False

    def _clear_all(self, key: str) -> None:
        self._save(key, [])

    # Timer methods
    def get_all_timers(self) -> List[Dict]:
        return self._get_all('timers')

    def get_timer(self, timer_id: str) -> Optional[Dict]:
        return self._get_one('timers', timer_id)

    def save_timer(self, timer_data: Dict) -> None:
        self._save_one('timers', timer_data)

    def remove_timer(self, timer_id: str) -> bool:
        return self._remove_one('timers', timer_id)

    def clear_timers(self) -> None:
        self._clear_all('timers')

    # Alarm methods
    def get_all_alarms(self) -> List[Dict]:
        return self._get_all('alarms')

    def get_alarm(self, alarm_id: str) -> Optional[Dict]:
        return self._get_one('alarms', alarm_id)

    def save_alarm(self, alarm_data: Dict) -> None:
        self._save_one('alarms', alarm_data)

    def remove_alarm(self, alarm_id: str) -> bool:
        return self._remove_one('alarms', alarm_id)

    def clear_alarms(self) -> None:
        self._clear_all('alarms')

    # Reminder methods
    def get_all_reminders(self) -> List[Dict]:
        return self._get_all('reminders')

    def get_reminder(self, reminder_id: str) -> Optional[Dict]:
        return self._get_one('reminders', reminder_id)

    def save_reminder(self, reminder_data: Dict) -> None:
        self._save_one('reminders', reminder_data)

    def remove_reminder(self, reminder_id: str) -> bool:
        return self._remove_one('reminders', reminder_id)

    def clear_reminders(self) -> None:
        self._clear_all('reminders')

    # Mention methods
    def get_all_mentions(self) -> List[Dict]:
        return self._get_all('mentions')

    def get_mention(self, mention_id: str) -> Optional[Dict]:
        return self._get_one('mentions', mention_id)

    def save_mention(self, mention_data: Dict) -> None:
        self._save_one('mentions', mention_data)

    def remove_mention(self, mention_id: str) -> bool:
        return self._remove_one('mentions', mention_id)

    def clear_mentions(self) -> None:
        self._clear_all('mentions')

    # Stats methods
    def get_stats(self) -> Dict:
        return self._load('stats')

    def increment_command_usage(self, command: str) -> None:
        """Increments the usage count for a command."""
        stats = self._load('stats')
        if not isinstance(stats, dict):
            stats = {}
        commands_used = stats.get('commands_used', {})
        commands_used[command] = commands_used.get(command, 0) + 1
        stats['commands_used'] = commands_used
        stats['total_commands'] = stats.get('total_commands', 0) + 1
        stats['last_command_time'] = datetime.now().isoformat()
        self._save('stats', stats)

    def increment_timers_created(self):
        """Увеличивает счетчик созданных таймеров."""
        stats = self.get_stats()
        stats['timers_created'] = stats.get('timers_created', 0) + 1
        self._save('stats', stats)

    def increment_alarms_created(self):
        """Увеличивает счетчик созданных будильников и напоминаний."""
        stats = self.get_stats()
        stats['alarms_created'] = stats.get('alarms_created', 0) + 1
        self._save('stats', stats)

    def increment_mentions_created(self):
        """Увеличивает счетчик созданных упоминаний и спама."""
        stats = self.get_stats()
        stats['mentions_created'] = stats.get('mentions_created', 0) + 1
        self._save('stats', stats)

    def get_command_usage(self, command: str) -> int:
        """Gets the usage count for a command."""
        stats = self._load('stats')
        commands_used = stats.get('commands_used', {})
        return commands_used.get(command, 0)

    def get_total_commands(self) -> int:
        """Gets the total number of commands used."""
        stats = self._load('stats')
        return stats.get('total_commands', 0)

    def get_last_command_time(self) -> str:
        """Gets the time of the last command."""
        stats = self._load('stats')
        return stats.get('last_command_time', '')
