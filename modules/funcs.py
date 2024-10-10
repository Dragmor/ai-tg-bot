"""
Разные функции
"""

import random
# 
from modules import bot_info
# импорт из файла __init__
from modules import ai
from modules import logger

async def send_message(bot, message, msg_text):
    sent_message = None
    try:
        try:
            sent_message = await message.reply(msg_text, parse_mode='Markdown')
        except Exception as error:
            logger.warning(f"Ошибка при отправке сообщения с parse_mode='Markdown': {error}, пробую отправить без parse_mode")
            sent_message = await message.reply(msg_text)
            logger.info("Удалось отправить сообщение без parse_mode")
    except Exception as e:
        logger.error(f'Ошибка при отправке сообщения: {e}')
    return sent_message


def split_message(message, max_length):
    """
    Разбивает сообщение на части, не превышающие max_length, стараясь разбивать по строкам.
    """
    lines = message.split('\n')
    messages = []
    current_message = ''
    for line in lines:
        # Добавляем 1 символ для '\n'
        if len(current_message) + len(line) + 1 <= max_length:
            if current_message:
                current_message += '\n' + line
            else:
                current_message = line
        else:
            # Если текущая строка не помещается, сохраняем накопленное сообщение
            if current_message:
                messages.append(current_message)
            # Проверяем, не превышает ли отдельная строка max_length
            while len(line) > max_length:
                messages.append(line[:max_length])
                line = line[max_length:]
            current_message = line
    if current_message:
        messages.append(current_message)
    return messages

async def send_split_messages(bot, message, messages):
    previous_message = None
    for msg_part in messages:
        try:
            if previous_message:
                sent_message = await send_message(bot=bot, message=previous_message, msg_text=msg_part)
            else:
                sent_message = await send_message(bot=bot, message=message, msg_text=msg_part)
            previous_message = sent_message
        except Exception as error:
            logger.error(f'Не удалось отправить часть сообщения: {error}')

def format_response(response):
    result = []
    for s in response.split('\n'):
        result.append(s)
        if "#" in s:
            result[-1] = f"`{result[-1].replace('#', '')}`"
        if s.startswith("-"):
            result[-1] = f"_{result[-1]}_"

    return "\n".join(result).replace("**", "*") if result else response.replace("**", "*")

# Функция определения, будет ли бот отвечать
async def should_reply(bot, message, text):
    # если боту ответили на его сообщение, то 100% отвечаем
    if message.reply_to_message and message.reply_to_message.from_user.id == bot_info.get_id():
        return 'reply'

    # если встречается подстрока из списка триггеров
    if text and any(substring in text for substring in ai.config.get("triggers", [])):
        return True

    # если это ЛС с ботом - возвращаем True, чтобы 100% ответил
    if message.chat.type == 'private':
        return True

    # иначе какой-то % что ответит
    return random.randint(0, 100) < 5  # 5% вероятность ответа