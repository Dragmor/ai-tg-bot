"""
обработка изображений из тг
"""

import base64
import requests
import random
# 
from modules import logger
# это импорт из __init__
from modules import bot, ai


async def process_image_message(message=None, img_url=None, prompt=None):
    if message:
        # Получаем самое большое изображение
        largest_photo = message.photo[-1]
        # Получаем информацию о файле
        file_info = await bot.get_file(largest_photo.file_id)
        # Скачиваем файл в память без сохранения на диск
        image_data = await bot.download_file(file_info.file_path)
        # Кодируем изображение в base64
        image = base64.b64encode(image_data.getvalue()).decode('utf-8')
        # получаем ответ от ИИ, что изображено
        img_info = ai.view_image(image=f"data:image/jpeg;base64,{image}", prompt=prompt) if image else None
    elif img_url:
        # получаем ответ от ИИ, что изображено по ссылке
        img_info = ai.view_image(image=img_url, prompt=prompt)
    else:
        await logger.debug(f"Не найдено изображения в сообщении для обработки!")
        return None

    return img_info
        