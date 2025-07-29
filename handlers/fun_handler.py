#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import random
import re
import hashlib
import json
import os
from typing import Dict, List, Optional
from telethon import TelegramClient

from utils.json_storage import JsonStorage
from config import config

logger = logging.getLogger(__name__)

class FunHandler:
    def __init__(self, bot):
        self.bot = bot
        
        # Загружаем данные для развлекательных команд
        self.quotes = self._load_quotes()
        self.jokes = self._load_jokes()
        self.ascii_templates = self._load_ascii_templates()
        
        # Данные для игр
        self.rps_choices = ['камень', 'ножницы', 'бумага', 'rock', 'paper', 'scissors']
        self.rps_mapping = {
            'камень': 'rock', 'ножницы': 'scissors', 'бумага': 'paper',
            'rock': 'rock', 'scissors': 'scissors', 'paper': 'paper'
        }
        
        self.ball_responses = [
            "🔮 Бесспорно!", "🔮 Предрешено!", "🔮 Никаких сомнений!",
            "🔮 Определенно да!", "🔮 Можешь быть уверен в этом!",
            "🔮 Мой ответ - да!", "🔮 Скорее всего!", "🔮 Хорошие перспективы!",
            "🔮 Знаки говорят - да!", "🔮 Да!", "🔮 Пока не ясно, попробуй снова!",
            "🔮 Спроси позже!", "🔮 Лучше не рассказывать!", "🔮 Сейчас нельзя предсказать!",
            "🔮 Сконцентрируйся и спроси опять!", "🔮 Не рассчитывай на это!",
            "🔮 Мой ответ - нет!", "🔮 Мои источники говорят - нет!",
            "🔮 Перспективы не очень хорошие!", "🔮 Весьма сомнительно!"
        ]
    
    def _load_quotes(self) -> List[str]:
        """Загружает цитаты из файла"""
        try:
            if os.path.exists(config.QUOTES_FILE):
                with open(config.QUOTES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('quotes', [])
        except Exception as e:
            logger.warning(f"Не удалось загрузить цитаты: {e}")
        
        # Дефолтные цитаты если файл не найден
        return [
            "💡 Единственный способ делать великие дела - это любить то, что ты делаешь. - Стив Джобс",
            "💡 Жизнь - это то, что происходит с тобой, пока ты строишь планы. - Джон Леннон", 
            "💡 Будь собой, остальные роли уже заняты. - Оскар Уайльд",
            "💡 Успех - это способность идти от неудачи к неудаче, не теряя энтузиазма. - Уинстон Черчилль",
            "💡 Не бойся совершать ошибки. Бойся не учиться на них.",
            "💡 Лучшее время посадить дерево было 20 лет назад. Второе лучшее время - сейчас.",
            "💡 Если хочешь идти быстро - иди один. Если хочешь идти далеко - идите вместе."
        ]
    
    def _load_jokes(self) -> List[str]:
        """Загружает шутки из файла"""
        try:
            if os.path.exists(config.JOKES_FILE):
                with open(config.JOKES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('jokes', [])
        except Exception as e:
            logger.warning(f"Не удалось загрузить шутки: {e}")
        
        # Дефолтные шутки если файл не найден  
        return [
            "😄 Почему программисты не любят природу? Слишком много багов!",
            "😄 - Что такое рекурсия? - А что такое рекурсия?",
            "😄 Программист приходит домой. Жена говорит: - Сходи в магазин, купи хлеб, если будут яйца - возьми десяток. Программист приходит с десятью батонами хлеба. - Зачем столько? - Яйца были...",
            "😄 HTTP 418: Я чайник! ☕",
            "😄 - Сколько программистов нужно, чтобы вкрутить лампочку? - Ни одного, это аппаратная проблема!",
            "😄 99 багов в коде, 99 багов! Исправь один, запуши в main... 127 багов в коде!",
            "😄 Есть только 10 типов людей в мире: те, кто понимает двоичную систему, и те, кто не понимает."
        ]
    
    def _load_ascii_templates(self) -> Dict[str, str]:
        """Загружает шаблоны ASCII арта"""
        try:
            if os.path.exists(config.ASCII_ART_FILE):
                with open(config.ASCII_ART_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Не удалось загрузить ASCII арт: {e}")
        
        # Дефолтные шаблоны
        return {
            "HELLO": """
 _   _ _____ _     _     ___  
| | | | ____| |   | |   / _ \ 
| |_| |  _| | |   | |  | | | |
|  _  | |___| |___| |__| |_| |
|_| |_|_____|_____|_____\___/ 
            """,
            "OK": """
 _____ _   _ 
|  _  | | / /
| | | | |/ / 
| |_| |    \ 
 \___/|_|\_\ 
            """
        }
    
    async def handle_quote(self, event):
        """Обработка команды /quote"""
        try:
            self.bot.storage.increment_command_usage('quote')
            
            quote = random.choice(self.quotes)
            await event.edit(quote)
            
            logger.info("Отправлена случайная цитата")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_quote: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при получении цитаты!")
    
    async def handle_joke(self, event):
        """Обработка команды /joke"""
        try:
            self.bot.storage.increment_command_usage('joke')
            
            joke = random.choice(self.jokes)
            await event.edit(joke)
            
            logger.info("Отправлена случайная шутка")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_joke: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при получении шутки!")
    
    async def handle_ascii(self, event):
        """Обработка команды /ascii"""
        try:
            self.bot.storage.increment_command_usage('ascii')
            
            text = event.pattern_match.group(1).strip().upper()
            
            if not text:
                await event.edit(f"{config.ERROR_EMOJI} Используйте: /ascii \"ТЕКСТ\"")
                return
            
            # Проверяем есть ли готовый шаблон
            if text in self.ascii_templates:
                ascii_art = self.ascii_templates[text]
            else:
                # Генерируем простой ASCII арт
                ascii_art = self._generate_simple_ascii(text)
            
            await event.edit(f"```\n{ascii_art}\n```")
            
            logger.info(f"Создан ASCII арт для: {text}")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_ascii: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при создании ASCII арта!")
    
    def _generate_simple_ascii(self, text: str) -> str:
        """Генерирует простой ASCII арт из текста"""
        # Простой ASCII арт - каждая буква в рамке
        lines = ["", "", ""]
        
        for char in text:
            if char == ' ':
                lines[0] += "   "
                lines[1] += "   "
                lines[2] += "   "
            else:
                lines[0] += f"┌─┐"
                lines[1] += f"│{char}│"
                lines[2] += f"└─┘"
        
        return "\n".join(lines)
    
    async def handle_rps(self, event):
        """Обработка команды /rps (камень-ножницы-бумага)"""
        try:
            self.bot.storage.increment_command_usage('rps')
            
            user_choice = event.pattern_match.group(1).strip().lower()
            
            if user_choice not in self.rps_choices:
                await event.edit(f"{config.ERROR_EMOJI} Выберите: камень, ножницы, бумага")
                return
            
            # Нормализуем выбор пользователя
            user_normalized = self.rps_mapping[user_choice]
            
            # Выбор бота
            bot_choices = ['rock', 'paper', 'scissors']
            bot_choice = random.choice(bot_choices)
            
            # Переводим обратно для отображения
            choice_names = {'rock': 'камень', 'paper': 'бумага', 'scissors': 'ножницы'}
            choice_emojis = {'rock': '🗿', 'paper': '📄', 'scissors': '✂️'}
            
            user_display = choice_names[user_normalized]
            bot_display = choice_names[bot_choice]
            
            # Определяем победителя
            if user_normalized == bot_choice:
                result = "🤝 Ничья!"
            elif (user_normalized == 'rock' and bot_choice == 'scissors') or \
                 (user_normalized == 'paper' and bot_choice == 'rock') or \
                 (user_normalized == 'scissors' and bot_choice == 'paper'):
                result = "🎉 Вы выиграли!"
            else:
                result = "😔 Вы проиграли!"
            
            message = f"""
🎮 **Камень-Ножницы-Бумага**

Вы: {choice_emojis[user_normalized]} {user_display}
Бот: {choice_emojis[bot_choice]} {bot_display}

{result}
            """.strip()
            
            await event.edit(message)
            
            logger.info(f"RPS: пользователь {user_display}, бот {bot_display}, результат: {result}")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_rps: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка в игре!")
    
    async def handle_coin(self, event):
        """Обработка команды /coin"""
        try:
            self.bot.storage.increment_command_usage('coin')
            
            result = random.choice(['орел', 'решка'])
            emoji = '🦅' if result == 'орел' else '👑'
            
            await event.edit(f"🪙 Подбрасываю монетку...\n\n{emoji} **{result.upper()}**!")
            
            logger.info(f"Монетка: {result}")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_coin: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при подбрасывании монетки!")
    
    async def handle_dice(self, event):
        """Обработка команды /dice"""
        try:
            self.bot.storage.increment_command_usage('dice')
            
            # Парсим максимальное значение
            max_value = 6  # По умолчанию обычный кубик
            match = event.pattern_match.group(1)
            if match:
                try:
                    max_value = int(match.strip())
                    if max_value < 2:
                        max_value = 2
                    elif max_value > 1000:
                        max_value = 1000
                except ValueError:
                    await event.edit(f"{config.ERROR_EMOJI} Неверное число!")
                    return
            
            result = random.randint(1, max_value)
            
            # Выбираем эмодзи в зависимости от результата
            if max_value == 6:
                dice_emojis = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
                emoji = dice_emojis[result - 1]
            else:
                emoji = '🎲'
            
            await event.edit(f"🎲 Бросаю кубик (1-{max_value})...\n\n{emoji} **{result}**!")
            
            logger.info(f"Кубик 1-{max_value}: {result}")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_dice: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при броске кубика!")
    
    async def handle_8ball(self, event):
        """Обработка команды /8ball"""
        try:
            self.bot.storage.increment_command_usage('8ball')
            
            question = event.pattern_match.group(1).strip()
            
            if not question:
                await event.edit(f"{config.ERROR_EMOJI} Задайте вопрос! Используйте: /8ball \"ваш вопрос?\"")
                return
            
            if not question.endswith('?'):
                question += '?'
            
            response = random.choice(self.ball_responses)
            
            message = f"""
🎱 **Магический шар предсказаний**

❓ *{question}*

{response}
            """.strip()
            
            await event.edit(message)
            
            logger.info(f"8ball вопрос: {question[:50]}...")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_8ball: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка в магическом шаре!")
    
    async def handle_random(self, event):
        """Обработка команды /random"""
        try:
            self.bot.storage.increment_command_usage('random')
            
            # Парсим диапазон
            min_val = 1
            max_val = 100
            
            match1 = event.pattern_match.group(1)  # первое число
            match2 = event.pattern_match.group(2)  # второе число
            
            if match1:
                try:
                    if match2:
                        # Два числа: /random 10 50
                        min_val = int(match1)
                        max_val = int(match2)
                    else:
                        # Одно число: /random 50 (от 1 до 50)
                        max_val = int(match1)
                except ValueError:
                    await event.edit(f"{config.ERROR_EMOJI} Неверные числа!")
                    return
            
            # Проверяем диапазон
            if min_val > max_val:
                min_val, max_val = max_val, min_val
            
            if max_val - min_val > 1000000:
                await event.edit(f"{config.ERROR_EMOJI} Слишком большой диапазон!")
                return
            
            result = random.randint(min_val, max_val)
            
            await event.edit(f"🎰 Случайное число от {min_val} до {max_val}:\n\n🎯 **{result}**")
            
            logger.info(f"Случайное число {min_val}-{max_val}: {result}")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_random: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка в генерации числа!")
    
    async def handle_hash(self, event):
        """Обработка команды /hash"""
        try:
            self.bot.storage.increment_command_usage('hash')
            
            text = event.pattern_match.group(1).strip()
            
            # Ищем алгоритм и текст
            # Формат: [algo] "text" или просто "text"
            parts = re.match(r'^(sha1|sha256|sha512|md5)\s+"?([^"]+)"?$', text, re.IGNORECASE)
            
            if parts:
                algo = parts.group(1).lower()
                text_to_hash = parts.group(2)
            else:
                # Если алгоритм не указан, по умолчанию md5
                algo = 'md5'
                text_to_hash = text.strip('"')

            if not text_to_hash:
                await event.edit(f"{config.ERROR_EMOJI} Укажите текст: `/hash \"мой текст\"`")
                return

            h = hashlib.new(algo)
            h.update(text_to_hash.encode('utf-8'))
            hashed_text = h.hexdigest()

            message = f"""
🧮 **Хеширование**

Алгоритм: `{algo.upper()}`
Хеш: `{hashed_text}`
            """.strip()

            await event.edit(message)
            logger.info(f"Сгенерирован хеш {algo} для текста: {text_to_hash[:20]}...")

        except Exception as e:
            logger.error(f"Ошибка в handle_hash: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при хешировании!")

    async def handle_calc(self, event):
        """Обработка команды /calc"""
        try:
            self.bot.storage.increment_command_usage('calc')
            
            expression = event.pattern_match.group(1).strip()
            
            if not expression:
                await event.edit(f"{config.ERROR_EMOJI} Введите выражение! Используйте: /calc 2+2*5")
                return
            
            # Очищаем выражение от небезопасных символов
            safe_expression = self._sanitize_math_expression(expression)
            
            if not safe_expression:
                await event.edit(f"{config.ERROR_EMOJI} Недопустимые символы в выражении!")
                return
            
            try:
                # Безопасное вычисление
                result = eval(safe_expression, {"__builtins__": {}}, {
                    "abs": abs, "round": round, "min": min, "max": max,
                    "pow": pow, "sqrt": lambda x: x**0.5
                })
                
                # Форматируем результат
                if isinstance(result, float):
                    if result.is_integer():
                        result = int(result)
                    else:
                        result = round(result, 8)
                
                await event.edit(f"🧮 **Калькулятор**\n\n`{expression}` = **{result}**")
                
                logger.info(f"Вычисление: {expression} = {result}")
                
            except ZeroDivisionError:
                await event.edit(f"{config.ERROR_EMOJI} Деление на ноль!")
            except (ValueError, TypeError, SyntaxError):
                await event.edit(f"{config.ERROR_EMOJI} Ошибка в выражении!")
            except Exception:
                await event.edit(f"{config.ERROR_EMOJI} Не удалось вычислить!")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_calc: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка в калькуляторе!")
    
    def _sanitize_math_expression(self, expression: str) -> Optional[str]:
        """Очищает математическое выражение от небезопасных символов"""
        # Разрешенные символы: цифры, операторы, скобки, точка
        allowed_chars = set('0123456789+-*/().% ')
        
        # Разрешенные функции
        allowed_functions = ['abs', 'round', 'min', 'max', 'pow', 'sqrt']
        
        # Убираем пробелы и проверяем символы
        clean_expr = ''.join(c for c in expression if c in allowed_chars or c.isalpha())
        
        # Проверяем на наличие запрещенных слов
        forbidden_words = ['import', 'exec', 'eval', 'open', 'file', '__']
        for word in forbidden_words:
            if word in clean_expr.lower():
                return None
        
        # Заменяем некоторые символы
        clean_expr = clean_expr.replace('^', '**')  # Степень
        
        return clean_expr if clean_expr else None
    
    async def handle_morning(self, event):
        """Обработка команды /morning [тип]"""
        try:
            self.bot.storage.increment_command_usage('morning')
            
            # Получаем аргумент (может быть None, пустой строкой или содержать значение)
            args = event.pattern_match.group(1)
            
            # Проверяем, что аргумент есть, не пустой и является числом от 1 до 3
            if not args or not args.strip().isdigit() or int(args.strip()) not in [1, 2, 3]:
                await event.edit(
                    f"{config.ERROR_EMOJI} Укажите тип утреннего сообщения (1-3):\n"
                    "1. Доброе утро всем\n"
                    "2. Доброе утро другу/кенту\n"
                    "3. Доброе утро девушке/подруге"
                )
                return

            msg_type = int(args.strip())
            
            # Сообщения для разных типов
            messages = {
                1: [
                    "Доброе утро всем! Хорошего дня! ☀️",
                    "Всем доброго утра и отличного настроения! 🌞",
                    "Доброе утро, народ! Пусть день будет продуктивным! 🌅",
                    "С добрым утром! Желаю всем удачного дня! 🌄",
                    "Доброе утро, компания! Да будет день прекрасным! 🌇"
                ],
                2: [
                    "Привет, брат! Доброе утро! Как спалось?",
                    "Эй, кент! Доброе утро! Готов к новому дню?",
                    "Йоу, дружище! Доброе утро! Как сам?",
                    "Привет, братан! Доброе утро! Как настроение?",
                    "Эй, кореш! Доброе утро! Как выспался?"
                ],
                3: [
                    "Доброе утро, солнышко! Хорошего тебе дня! 💖",
                    "Привет, красавица! Доброе утро! 🌹",
                    "Доброе утро, родная! Пусть день будет чудесным! 💕",
                    "Привет, зайка! Доброе утро! Как спалось? 🌸",
                    "Доброе утро, любимая! Хорошего настроения! 💝"
                ]
            }
            
            # Выбираем случайное сообщение из выбранного типа
            message = random.choice(messages[msg_type])
            await event.edit(message)
            
            logger.info(f"Отправлено утреннее сообщение типа {msg_type}")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_morning: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при отправке утреннего сообщения!")
    
    async def handle_hash(self, event):
        """Обработка команды /hash"""
        try:
            self.bot.storage.increment_command_usage('hash')
            
            # Простая реализация хеширования
            # В реальном проекте лучше вынести в отдельный модуль
            args = event.text.split(' ', 2)
            if len(args) < 2:
                await event.edit(f"{config.ERROR_EMOJI} Используйте: /hash \"текст\" или /hash md5 \"текст\"")
                return
            
            # Определяем тип хеша и текст
            if len(args) == 2:
                hash_type = 'md5'
                text = args[1].strip('"\'')
            else:
                hash_type = args[1].lower()
                text = args[2].strip('"\'')
            
            if not text:
                await event.edit(f"{config.ERROR_EMOJI} Текст для хеширования не может быть пустым!")
                return
            
            # Вычисляем хеш
            text_bytes = text.encode('utf-8')
            
            if hash_type == 'md5':
                hash_result = hashlib.md5(text_bytes).hexdigest()
            elif hash_type == 'sha1':
                hash_result = hashlib.sha1(text_bytes).hexdigest()
            elif hash_type == 'sha256':
                hash_result = hashlib.sha256(text_bytes).hexdigest()
            elif hash_type == 'sha512':
                hash_result = hashlib.sha512(text_bytes).hexdigest()
            else:
                await event.edit(f"{config.ERROR_EMOJI} Поддерживаемые типы: md5, sha1, sha256, sha512")
                return
            
            # Обрезаем текст для отображения если он слишком длинный
            display_text = text if len(text) <= 50 else text[:47] + "..."
            
            message = f"""
🔐 **Хеширование {hash_type.upper()}**

📝 Текст: `{display_text}`
🔑 Хеш: `{hash_result}`
            """.strip()
            
            await event.edit(message)
            
            logger.info(f"Хеширование {hash_type}: текст длиной {len(text)} символов")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_hash: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при хешировании!")
    
    async def handle_meme(self, event):
        """Обработка команды /meme"""
        try:
            self.bot.storage.increment_command_usage('meme')
            
            memes = [
                "🐸 It's Wednesday, my dudes!",
                "🔥 This is fine. 🔥",
                "📈 Stonks 📈",
                "🚀 To the moon! 🚀",
                "💎 Diamond hands! 💎🙌",
                "📉 Buy the dip! 📉",
                "🤖 Beep boop, I'm a bot!",
                "⚡ Unlimited power! ⚡",
                "🎯 Task failed successfully!",
                "💻 It works on my machine!",
                "🐛 It's not a bug, it's a feature!",
                "☕ Have you tried turning it off and on again?",
                "🔄 Loading... 99%",
                "❌ Error 404: Motivation not found",
                "🎮 Git gud!",
                "🏆 Achievement unlocked: Procrastination Master!",
            ]
            
            meme = random.choice(memes)
            await event.edit(meme)
            
            logger.info("Отправлен случайный мем")
            
        except Exception as e:
            logger.error(f"Ошибка в handle_meme: {e}")
            await event.edit(f"{config.ERROR_EMOJI} Ошибка при получении мема!")
    
    async def save_custom_content(self, content_type: str, content: str):
        """Сохраняет пользовательский контент"""
        try:
            if content_type == 'quote':
                self.quotes.append(content)
                await self._save_quotes()
            elif content_type == 'joke':
                self.jokes.append(content)
                await self._save_jokes()
            
            logger.info(f"Добавлен новый {content_type}: {content[:50]}...")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения {content_type}: {e}")
    
    async def _save_quotes(self):
        """Сохраняет цитаты в файл"""
        try:
            os.makedirs(os.path.dirname(config.QUOTES_FILE), exist_ok=True)
            with open(config.QUOTES_FILE, 'w', encoding='utf-8') as f:
                json.dump({'quotes': self.quotes}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения цитат: {e}")
    
    async def _save_jokes(self):
        """Сохраняет шутки в файл"""
        try:
            os.makedirs(os.path.dirname(config.JOKES_FILE), exist_ok=True)
            with open(config.JOKES_FILE, 'w', encoding='utf-8') as f:
                json.dump({'jokes': self.jokes}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения шуток: {e}")