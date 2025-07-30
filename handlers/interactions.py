#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import random
from typing import Optional

from telethon import events
from telethon.tl import types

from config import config

logger = logging.getLogger(__name__)

class InteractionsHandler:
    def __init__(self, bot):
        self.bot = bot
        self.interactions = self._load_interactions()
        logger.info("Инициализирован обработчик интеракций")
    
    def _load_interactions(self) -> dict:
        """Загружает данные для интеракций из JSON файла"""
        try:
            if os.path.exists(config.INTERACTIONS_FILE):
                logger.info(f"Загрузка интеракций из {config.INTERACTIONS_FILE}")
                with open(config.INTERACTIONS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Загружено {len(data.get('insults', []))} оскорблений и {len(data.get('roasts', []))} 'прожариваний'")
                    return data
        except Exception as e:
            logger.error(f"Не удалось загрузить файл интеракций: {e}", exc_info=True)
        
        logger.warning("Используются пустые списки интеракций")
        return {"insults": [], "roasts": [], "ship": {}, "compliment": []}
    
    async def _get_user_mention(self, event, user_entity=None, username=None, first_name=None, target_text=None):
        """
        Возвращает упоминание пользователя с именем и кликабельным юзернеймом
        :param event: Событие сообщения (для получения клиента)
        :param user_entity: Объект пользователя Telethon (если есть)
        :param username: Юзернейм пользователя (без @)
        :param first_name: Имя пользователя
        :param target_text: Текст цели (может быть @username или просто текст)
        """
        try:
            # Если передан объект пользователя, используем его
            if user_entity:
                display_name = getattr(user_entity, 'first_name', None) or \
                             getattr(user_entity, 'username', None) or \
                             f"user{user_entity.id}" if hasattr(user_entity, 'id') else "кто-то"
                return f"[{display_name}](tg://user?id={user_entity.id})"
                
            # Если передан текст цели
            if target_text is not None:
                # Если это юзернейм (начинается с @), пробуем найти пользователя
                if target_text.startswith('@'):
                    try:
                        user = await event.client.get_entity(target_text)
                        if user:
                            display_name = getattr(user, 'first_name', None) or target_text[1:]
                            return f"[{display_name}](tg://user?id={user.id})"
                    except Exception as e:
                        logger.debug(f"Не удалось найти пользователя {target_text}: {e}")
                    return target_text  # Возвращаем как есть, если не нашли пользователя
                # Если это просто текст, возвращаем как есть
                return target_text
                
            # Если передан только username, возвращаем его с @
            if username:
                return f"@{username}"
                
            # Если передано только имя, возвращаем его
            if first_name:
                return first_name
                
        except Exception as e:
            logger.error(f"Ошибка в _get_user_mention: {e}", exc_info=True)
            
        return "кто-то"

    async def _get_target_name(self, event, target: str) -> str:
        """
        Получает имя цели для интеракции
        :param event: Событие сообщения
        :param target: Текст цели (обязательный параметр)
        :return: Отформатированное имя цели
        """
        return await self._get_user_mention(event, target_text=target)

    async def _get_gayrate_message(self, target: str) -> str:
        """
        Генерирует сообщение с рейтингом гея для пользователя
        :param target: Цель (юзернейм или текст)
        :return: Строка с результатом
        """
        # Генерируем случайный процент
        percent = random.randint(1, 100)
        
        # Выбираем категорию на основе процента
        if percent >= 90:
            category = "moreThan90"
        elif percent >= 70:
            category = "between70And89"
        elif percent >= 50:
            category = "between50And69"
        elif percent >= 30:
            category = "between30And49"
        else:
            category = "lessThan30"
        
        # Получаем список фраз для выбранной категории
        phrases = self.interactions.get("gayrate", {}).get(category, [])
        
        # Если фраз нет, используем стандартное сообщение
        if not phrases:
            return f"🌈 Гей-рейтинг для {target}:\n💖 Вероятность: {percent}%\n\n{target} — интересный случай!"
        
        # Выбираем случайную фразу и подставляем цель
        phrase = random.choice(phrases).format(target=target, percent=percent)
        
        # Добавляем заголовок с процентом, если его еще нет в фразе
        if "%" not in phrase:
            return f"🌈 Гей-рейтинг для {target}:\n💖 Вероятность: {percent}%\n\n{phrase}"
        return phrase

    async def _get_commit_message(self, commit_type: str = None, custom_message: str = None) -> str:
        """
        Генерирует сообщение о коммите
        :param commit_type: Тип коммита (feat, fix, docs и т.д.)
        :param custom_message: Кастомное сообщение (если есть)
        :return: Строка с сообщением о коммите
        """
        # Если тип не указан, выбираем случайный из доступных
        if not commit_type or commit_type.lower() == 'random':
            commit_type = random.choice(list(self.interactions.get("commit", {}).keys()))
        
        # Получаем сообщение в зависимости от типа коммита
        messages = self.interactions.get("commit", {}).get(commit_type, [])
        
        if not messages:
            # Если нет сообщений для этого типа, используем общий шаблон
            commit_message = f"{commit_type}: {custom_message if custom_message else 'no message provided'}"
        else:
            # Выбираем случайное сообщение для этого типа коммита
            commit_message = random.choice(messages)
            if custom_message:
                commit_message = f"{commit_type}: {custom_message}"
            else:
                commit_message = f"{commit_type}: {commit_message}"
        
        return commit_message

    async def _get_define_message(self, event, target: str = None) -> str:
        # Get display name using the same method as other commands
        display_name = await self._get_target_name(event, target) if target else "Пользователь"
        last_message = None
        
        # Try to get last message from the current chat if target is a user mention
        if target and target.startswith('@'):
            try:
                # Get the user entity from the mention
                username = target.lstrip('@')
                
                # First, try to find the user in the current chat
                chat = await event.get_chat()
                logger.info(f"Ищем пользователя с ником @{username} в чате {chat.id}")
                
                found_user = None
                async for user in event.client.iter_participants(chat):
                    logger.debug(f"Проверяем пользователя: {getattr(user, 'username', 'no_username')} (ID: {user.id})")
                    if user.username and user.username.lower() == username.lower():
                        found_user = user
                        logger.info(f"Найден пользователь: {user.username} (ID: {user.id})")
                        break
                
                if found_user:
                    # Search for the last message from this user
                    logger.info(f"Ищем последнее сообщение от пользователя {found_user.id}")
                    try:
                        # First try to get the most recent message from the current chat
                        last_message = None
                        
                        # Search in current chat first
                        try:
                            messages = await event.client.get_messages(
                                chat,
                                from_user=found_user,
                                limit=100  # Get last 100 messages to find a good one
                            )
                            
                            # Find the first non-command message
                            for msg in messages:
                                if msg.text and msg.text.strip() and not msg.text.startswith('/'):
                                    last_message = msg.text
                                    logger.info(f"Найдено сообщение: {last_message}")
                                    break
                                
                        except Exception as e:
                            logger.warning(f"Ошибка поиска сообщений: {e}")
                        
                        # If we have a message, truncate if needed
                        if last_message and len(last_message) > 100:
                            last_message = last_message[:97] + '...'
                    except Exception as e:
                        logger.error(f"Ошибка получения сообщений: {e}")
                else:
                    logger.warning(f"Пользователь с ником @{username} не найден в чате")
            except Exception as e:
                logger.warning(f"Не удалось получить последнее сообщение для {target}: {e}")
        
        # Get random elements from each category
        base_template = random.choice(self.interactions.get("define", {}).get("base", [""]))
        habitat = random.choice(self.interactions.get("define", {}).get("habitat", [""]))
        
        # Get 3 random synonyms
        synonyms = random.sample(
            self.interactions.get("define", {}).get("synonyms", []),
            min(3, len(self.interactions.get("define", {}).get("synonyms", [])))
        )
        
        # Format templates with display_name
        try:
            base = base_template.format(target=display_name, user=display_name)
        except (KeyError, IndexError):
            base = base_template
            
        fact_template = random.choice(self.interactions.get("define", {}).get("facts", [""]))
        note_template = random.choice(self.interactions.get("define", {}).get("notes", [""]))
        
        try:
            fact = fact_template.format(target=display_name, user=display_name)
        except (KeyError, IndexError):
            fact = fact_template
            
        try:
            note = note_template.format(target=display_name, user=display_name)
        except (KeyError, IndexError):
            note = note_template
            
        log_label = random.choice(self.interactions.get("define", {}).get("log_labels", [""]))
        
        # Generate random stats
        cringe_level = random.randint(1, 100)
        trust_rating = random.randint(-100, 100)
        
        # IQ with 15% chance of NaN and 1% chance of negative
        iq_roll = random.random()
        if iq_roll < 0.15:
            iq = "NaN"
        elif iq_roll < 0.16:  # 1% chance of negative
            iq = f"-{random.randint(1, 300)}"
        else:
            iq = str(random.randint(1, 200))
        
        # Format the message
        message_parts = [
            f"📚 {base}",
            habitat,
            "",
            f"Синонимы: {', '.join(synonyms)}",
            f"Факт: {fact}\n",
            f"{'' if any(word in note for word in ['Внимание:', 'Предупреждение:', 'Осторожно:', 'Важно:', 'Уведомление:', 'Предостережение:']) else 'Заметка: '}{note}",
            "",
            f"📈 Уровень кринжа: {cringe_level}%",
            f"🔒 Рейтинг доверия: {trust_rating}",
            f"🧠 IQ по мнению бота: `{iq}`",
        ]
        
        if last_message:
            message_parts.append(f'💬 Последнее зафиксированное сообщение: "{last_message}"')
        else:
            message_parts.append('💬 У примата нет сообщений')
            
        message_parts.append(f'🎖️ Чаще всего упоминается в логах как: `{log_label}`')
        
        return "\n".join(message_parts)

    async def _get_ship_message(self, target1: str, target2: str) -> str:
        """
        Генерирует сообщение о совместимости двух пользователей
        :param target1: Первая цель (юзернейм или текст)
        :param target2: Вторая цель (юзернейм или текст)
        :return: Строка с результатом совместимости
        """
        # Генерируем случайный процент совместимости
        percent = random.randint(1, 100)
        
        # Выбираем категорию сообщения на основе процента
        if percent > 90:
            category = "moreThan90"
        elif percent > 70:
            category = "between70And89"
        elif percent > 50:
            category = "between50And69"
        elif percent > 30:
            category = "between30And49"
        else:
            category = "lessThan30"
        
        # Выбираем случайное сообщение из категории
        messages = self.interactions.get("ship", {}).get(category, [])
        
        # Формируем заголовок с процентом совместимости
        header = f"💘 Иследуемая пара: {target1} и {target2}:\n"
        header += f"🔮 Совместимость: {percent}%\n\n"
        
        # Если есть сообщение из категории, добавляем его, иначе используем заглушку
        if messages:
            message = random.choice(messages)
            message = message.format(
                target1=target1, 
                target2=target2, 
                percent=percent
            )
        else:
            message = f"{target1} и {target2} - {percent}% совместимы!"
        
        return header + message

    async def send_interaction(self, event, interaction_type: str, target: Optional[str] = None, target2: Optional[str] = None):
        """
        Отправляет случайную интеракцию указанного типа
        :param event: Событие сообщения
        :param interaction_type: Тип интеракции (insult, roast, ship, compliment, gayrate)
        :param target: Первая цель (обязательна для всех команд)
        :param target2: Вторая цель (только для ship)
        """
        try:
            # Проверяем, что цель указана (кроме команд, где есть своя проверка)
            if not target and interaction_type not in ['ship', 'commit']:
                await event.edit(f"⚠️ Неправильное использование команды.\nИспользование: /{interaction_type} @username или текст")
                return
            
            # Обрабатываем команду ship (две цели)
            if interaction_type == 'ship':
                if not target or not target2:
                    await event.edit("❌ Для команды /ship укажите две цели через пробел (юзернеймы или текст).")
                    return
                
                # Получаем имена целей
                target1_name = await self._get_target_name(event, target)
                target2_name = await self._get_target_name(event, target2)
                
                # Получаем сообщение о совместимости
                message = await self._get_ship_message(target1_name, target2_name)
            # Обрабатываем команду commit
            elif interaction_type == 'commit':
                # Если не указаны аргументы, показываем справку
                if not target:
                    help_text = (
                        "❌ Неправильное использование команды.\n\n"
                        "ℹ️ Доступные типы коммитов:\n"
                        "• `feat` - новая функциональность\n"
                        "• `fix` - исправление ошибок\n"
                        "• `docs` - изменения в документации\n"
                        "• `style` - форматирование, отсутствие изменений в коде\n"
                        "• `refactor` - рефакторинг кода\n"
                        "• `test` - добавление тестов\n"
                        "• `chore` - обновление задач сборки, настройки пакетов\n"
                        "• `perf` - изменения, улучшающие производительность\n"
                        "• `ci` - настройки CI и работа со скриптами\n"
                        "• `random` - случайный тип коммита\n\n"
                        "📌 Примеры использования:\n"
                        "• `/commit feat добавил новую кнопку`\n"
                        "• `/commit fix исправлена ошибка входа`\n"
                        "• `/commit random` - случайный коммит"
                    )
                    await event.edit(help_text)
                    return
                
                # Разбиваем сообщение на тип и текст
                parts = target.split(' ', 1)
                commit_type = parts[0].lower()
                custom_message = parts[1] if len(parts) > 1 else None
                
                # Генерируем сообщение о коммите
                commit_message = await self._get_commit_message(commit_type, custom_message)
                
                # Получаем информацию о пользователе
                sender = await event.get_sender()
                username = f"@{sender.username}" if hasattr(sender, 'username') and sender.username else "Unknown User"
                
                # Формируем финальное сообщение
                from datetime import datetime
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                message = (
                    f"✅ Коммит выполнен:\n"
                    f"🔨 {commit_message}\n"
                    f"🕐 Время коммита: {current_time}\n"
                    f"🧠 Автор: {username}\n"
                    f"📁 Ветка: main"
                )
                
                await event.edit(message)
                return
                
            # Обрабатываем команду define
            elif interaction_type == 'define':
                if not target:
                    await event.edit("ℹ️ Использование: /define @username или /define текст")
                    return
                    
                message = await self._get_define_message(event, target)
                await event.edit(message)
                return
                
                # Получаем имя цели
                target_name = await self._get_target_name(event, target)
                
                # Получаем сообщение с рейтингом
                message = await self._get_gayrate_message(target_name)
            else:
                # Получаем имя цели
                target_name = await self._get_target_name(event, target)
                
                # Выбираем случайное сообщение из соответствующего списка
                messages = self.interactions.get(interaction_type, [])
                if not messages:
                    await event.edit("❌ Не найдено сообщений для этой команды.")
                    return
                
                message = random.choice(messages).format(target=target_name)
            
            # Отправляем сообщение, редактируя исходное
            await event.edit(message)
            logger.debug("Сообщение успешно отправлено")
            
        except Exception as e:
            error_msg = f"Ошибка при обработке команды {interaction_type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            try:
                await event.edit("⚠️ Произошла ошибка при обработке команды.")
            except:
                logger.critical("Не удалось отправить сообщение об ошибке", exc_info=True)

def setup(bot):
    """Функция для инициализации хендлера"""
    logger.info("Настройка обработчика интеракций")
    return InteractionsHandler(bot)