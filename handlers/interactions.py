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
        :param interaction_type: Тип интеракции (insult, roast, ship, compliment)
        :param target: Первая цель (обязательна для всех команд)
        :param target2: Вторая цель (только для ship)
        """
        logger.info(f"Обработка команды {interaction_type} для цели: {target} и {target2 or 'нет второй цели'}")
        
        # Проверка на пустую цель
        if not target or not target.strip():
            usage_text = (
                f"⚠️ Неправильное использование команды.\n"
                f"Использование: /{interaction_type} @username или текст\n"
            )
            await event.edit(usage_text)
            return
            
        # Специальная обработка для команды ship
        if interaction_type == "ship":
            if not target2 or not target2.strip():
                await event.edit("⚠️ Для ship нужны две цели!\nПример: /ship @user1 @user2")
                return
                
            try:
                target1_name = await self._get_target_name(event, target)
                target2_name = await self._get_target_name(event, target2)
                message = await self._get_ship_message(target1_name, target2_name)
                await event.edit(message)
                logger.info(f"Отправлено сообщение ship: {message[:100]}...")
            except Exception as e:
                logger.error(f"Ошибка при обработке ship: {e}", exc_info=True)
                await event.edit("⚠️ Произошла ошибка при обработке команды ship.")
            return
            
        # Обработка команд с одной целью (insult, roast, compliment)
        interactions = self.interactions.get(interaction_type, [])
        if not interactions:
            error_msg = f"Нет доступных интеракций типа: {interaction_type}"
            logger.error(error_msg)
            await event.edit("⚠️ Извините, что-то пошло не так. Попробуйте позже.")
            return
        
        try:
            target_name = await self._get_target_name(event, target)
            logger.debug(f"Сгенерировано имя цели: {target_name}")
            
            message = random.choice(interactions).format(target=target_name)
            logger.info(f"Отправка сообщения типа {interaction_type}: {message[:100]}...")
            
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