"""
Класс для работы с АПИ Mistral, основной класс ИИ
"""

import os
import requests
import json
import time
import random
# 
import tiktoken
# 
from modules import logger


class AI():
    def __init__(self, api_key, history_file, config_file):
        self.api_key = api_key
        self.api_endpoint = 'https://api.mistral.ai/v1/chat/completions'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }
        self.history_file = history_file
        self.messages = self.load_history()
        self.config_file = config_file
        self.config = self.load_config()

    def load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return []

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # дефолтные настройки
            return {
                "model": 'mistral-large-latest',
                "vision": "pixtral-12b-2409",
                "triggers": [],
                "max_tokens": 2048,
                "prefix": None,
                "system_prompt": []
                }

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)

    # подсчитывает токены, и обрезает
    def count_tokens(self):
        total = []
        for content in self.config.get("system_prompt") + self.messages:
            total.append(content['content'])
        if self.config.get("prefix", None):
            total.append(self.config.get("prefix"))

        encoding = tiktoken.encoding_for_model("gpt-3.5")
        num_tokens = len(encoding.encode("\n".join(total)))

        return num_tokens

    # добавляет в историю сообщений
    def add_message(self, text, role='user'):
        if text:
            self.messages.append({'role': role, 'content': text})

    def view_image(self, image, prompt=None):
        # Подготовка сообщения для API
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt if prompt else "Нужно максимально подробное описание изображения и всего его содержимого. Если на изображении есть текст, то также напиши этот текст полностью."
                    },
                    {
                        "type": "image_url",
                        "image_url": image
                    }
                ]
            }
        ]

        # Подготовка запроса к API
        payload = {
            'model': self.config.get('vision'),
            'messages': messages,
            'temperature': 0.3,
            'top_p': 1,
            'random_seed': random.randint(0, 4096),
            'safe_prompt': False
        }

        # Отправка запроса к Mistral AI API
        response = requests.post(self.api_endpoint, headers=self.headers, json=payload)
        completion = response.json()

        # Проверяем успешность запроса
        if response.status_code == 200:
            result = completion['choices'][0]['message']['content']
            return result
        # 429 это превышен лимит на обращения к апи
        elif response.status_code == 429:
            logger.debug("Превышен лимит использования АПИ, ждём...")
            time.sleep(5)
        elif response.status_code == 500:
            logger.error(f"Неизвестная ошибка (статускод 500): {response.text}")
            return None
        else:
            # Обработка ошибок
            logger.error(f"Запрос к API вернул ошибку {response.status_code}: {response.text}")
            return None
        return self.view_image(image=image)

    def send_message(self, message=None, max_tokens=None):
        if message:
            self.add_message(text=message, role='user')

        if not max_tokens:
            max_tokens = self.config.get("max_tokens", 2048)

        prefix = [{"role": "assistant", "content": f"{self.config.get('prefix')}: ", "prefix": True}] if self.config.get("prefix", None) else []

        # эта функция подрежет память (скомпрессирует), если используется токенов больше чем пределтное кол-во
        self.compress_history()

        payload = {
            'model': self.config.get('model'),
            'messages': self.config.get("system_prompt") + self.messages + prefix,
            'temperature': 0.7,
            'top_p': 1,
            'max_tokens': max_tokens,
            'random_seed': random.randint(0, 4096),
            'safe_prompt': False
        }

        response = requests.post(self.api_endpoint, headers=self.headers, json=payload)
        completion = response.json()

        # logger.debug(f"токенов: всего {completion['usage']['total_tokens']}\nв запросе {completion['usage']['prompt_tokens']}\nв ответе {completion['usage']['completion_tokens']}")
        # logger.debug(f"токенов насчитано в tiktoken: {self.count_tokens()}")

        if response.status_code == 200:
            message = completion['choices'][0]['message']['content']
            if self.config.get("prefix", None):
                # обрезаю префикс
                message = message[len(self.config.get("prefix"))+2:]
            self.add_message(text=message, role='assistant')
            return message
        # 429 это превышен лимит на обращения к апи
        elif response.status_code == 429:
            logger.debug("Превышен лимит использования АПИ, ждём...")
            time.sleep(5)
        elif response.status_code == 500:
            logger.error(f"Неизвестная ошибка (статускод 500): {response.text}")
            return None
        elif response.status_code == 400:
            if "too large" in completion.get('message', ''):
                # Обрезаем сообщения, оставляя вторую половину
                logger.warning(f"Слишком большой контекст ({len(self.messages)} сообщений), удаляем первое сообщение... Текст ошибки: {completion.get('message')}")
                # выполняем компрессию памяти
                self.compress_history()
            else:
                logger.error(f'Ошибка 400: {response.text}')
                return None
        else:
            logger.error(f'Ошибка {response.status_code}: {response.text}')
            return None
        return self.send_message()

    def compress_history(self):
        """
        метод для компрессии памяти ИИ, когда её размер превышает макс. кол-во
        входных токенов
        """

        # если кол-во токенов не превышает максимум для модели - продолжаем без компрессии
        if (used_tokens:=self.count_tokens()) < 32000:
            return True
        else:
            logger.debug(f"Сейчас будет произведена компрессия памяти. Токенов в памяти до компрессии: {used_tokens}")

        # Выбираем часть сообщений для сжатия (первые 50% сообщений)
        num_messages_to_compress = len(self.messages) // 2
        messages_to_compress = self.messages[:num_messages_to_compress]

        # Формируем текст для сжатия
        text_to_summarize = ""
        for msg in messages_to_compress:
            text_to_summarize += f"{msg['role']}: {msg['content']}\n"

        # Создаем запрос для сжатия
        summary_prompt = [
            {
                'role': 'system',
                'content': 'Пожалуйста, сделай максимально-подробное резюме следующего диалога, сохраняя все важные детали и информацию'
            },
            {
                'role': 'user',
                'content': text_to_summarize
            }
        ]

        payload = {
            'model': self.config.get('model'),
            'messages': summary_prompt,
            'temperature': 0.5,
            'top_p': 1,
            'safe_prompt': False
        }

        response = requests.post('https://api.mistral.ai/v1/chat/completions', headers=self.headers, json=payload)
        if response.status_code == 200:
            completion = response.json()
            summary = completion['choices'][0]['message']['content']
            # Заменяем сжатые сообщения на резюме
            self.messages = [{'role': 'system', 'content': summary}] + self.messages[num_messages_to_compress:]
            logger.debug(f"Произведено сжатие памяти. Токенов после компрессии {self.count_tokens()}, сжатая история: {summary}")
            return True
        # 429 это превышен лимит на обращения к апи
        elif response.status_code == 429:
            logger.debug("Превышен лимит использования АПИ, ждём...")
            time.sleep(5)
        elif response.status_code == 500:
            logger.error(f"Неизвестная ошибка (статускод 500): {response.text}")
            return None
        elif response.status_code == 400:
            logger.error(f'Ошибка 400: {response.text}')
            return None
        else:
            logger.error(f'Ошибка {response.status_code}: {response.text}')
            return None
        return self.compress_history()