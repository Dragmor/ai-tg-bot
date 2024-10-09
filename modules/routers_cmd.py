"""
Содержит роутеры для настройки бота (команды для управления поведением и т.д.)
"""

from aiogram import types, Router
# 
from modules import bot, dp, router
from modules import decorators
from modules import ai


# Обработчик команды очистки памяти
@router.message(lambda msg: msg.text == '/clear' if msg.text else False)
@decorators.lock_thread
async def clear_memory(message: types.Message):
    ai.messages = []
    ai.save_history()
    await message.reply("`✅`", parse_mode='Markdown')



# показать триггеры
@router.message(lambda msg: msg.text == '/trigs' if msg.text else False)
async def check_triggers(message: types.Message):
    await message.reply(', '.join(ai.config["triggers"]) if ai.config.get("triggers") else "Триггеры не заданы!")

# Обработчик команды добавления триггера
@router.message(lambda msg: msg.text.startswith('/addtrig') if msg.text else False)
@decorators.lock_thread
async def add_trigger(message: types.Message):
    # Разделяем сообщение на части
    args = message.text.split(maxsplit=1)
    # Проверяем, заданы ли все необходимые параметры
    if len(args) < 2:
        await message.reply("*Используйте команду в формате:* `/addtrig` `<новый триггер>`", parse_mode='Markdown')
        return
    trigger = args[1]
    # Задаем новый системный промпт
    ai.config["triggers"].append(trigger.lower())
    ai.save_config()
    await message.reply("`✅`", parse_mode='Markdown')

# Обработчик команды удаления триггера
@router.message(lambda msg: msg.text.startswith('/deltrig') if msg.text else False)
@decorators.lock_thread
async def del_trigger(message: types.Message):
    # Разделяем сообщение на части
    args = message.text.split(maxsplit=1)
    # Проверяем, заданы ли все необходимые параметры
    if len(args) < 2:
        await message.reply("*Используйте команду в формате:* `/deltrig` `<триггер для удаления>`", parse_mode='Markdown')
        return
    trigger = args[1]
    if trigger.lower() not in ai.config["triggers"]:
        await message.reply("*Указанный триггер не найден в списке триггеров!*\nПросмотреть список триггеров можно командой: /trigs", parse_mode='Markdown')
        return
    # Задаем новый системный промпт
    ai.config["triggers"].remove(trigger.lower())
    ai.save_config()
    await message.reply("`✅`", parse_mode='Markdown')

# удалить все триггеры
@router.message(lambda msg: msg.text == '/cleartrigs' if msg.text else False)
@decorators.lock_thread
async def clear_triggers(message: types.Message):
    ai.config["triggers"] = []
    ai.save_config()
    await message.reply("`✅`", parse_mode='Markdown')



# показать системный промпт
@router.message(lambda msg: msg.text == '/sys' if msg.text else False)
async def check_system(message: types.Message):
    await message.reply(ai.config["system_prompt"][0]['content'] if ai.config.get("system_prompt") else "Нет системного промпта!")

# удалить системный промпт
@router.message(lambda msg: msg.text == '/delsys' if msg.text else False)
@decorators.lock_thread
async def delete_system(message: types.Message):
    ai.config["system_prompt"] = []
    ai.save_config()
    await message.reply("`✅`", parse_mode='Markdown')

# Обработчик команды смены системного промпта
@router.message(lambda msg: msg.text.startswith('/setsys') if msg.text else False)
@decorators.lock_thread
async def set_system(message: types.Message):
    # Разделяем сообщение на части
    args = message.text.split(maxsplit=1)
    # Проверяем, заданы ли все необходимые параметры
    if len(args) < 2:
        await message.reply("*Используйте команду в формате:* `/setsys` `<системный промпт>`", parse_mode='Markdown')
        return
    system_prompt = args[1]
    # Задаем новый системный промпт
    ai.config["system_prompt"] = [{
        'role': 'system', 'content': f"{system_prompt}"
    }]
    ai.save_config()
    await message.reply("`✅`", parse_mode='Markdown')



# показать префикс
@router.message(lambda msg: msg.text == '/pref' if msg.text else False)
async def check_prefix(message: types.Message):
    await message.reply(ai.config.get("prefix", None) or "Нет префикса!")

# удалить префикс
@router.message(lambda msg: msg.text == '/delpref' if msg.text else False)
@decorators.lock_thread
async def delete_prefix(message: types.Message):
    ai.config["prefix"] = []
    ai.save_config()
    await message.reply("`✅`", parse_mode='Markdown')

# Обработчик команды смены префикса
@router.message(lambda msg: msg.text.startswith('/setpref') if msg.text else False)
@decorators.lock_thread
async def set_prefix(message: types.Message):
    # Разделяем сообщение на части
    args = message.text.split(maxsplit=1)
    # Проверяем, заданы ли все необходимые параметры
    if len(args) < 2:
        await message.reply("*Используйте команду в формате:* `/setpref` `<роль>`", parse_mode='Markdown')
        return
    # Задаем новый префикс
    ai.config["prefix"] = args[1]
    ai.save_config()
    await message.reply("`✅`", parse_mode='Markdown')



# задать макс кол-во токенов
@router.message(lambda msg: msg.text.startswith('/maxtokens') if msg.text else False)
@decorators.lock_thread
async def change_max_tokens(message: types.Message):
    # Разделяем сообщение на части
    args = message.text.split(maxsplit=1)
    # Проверяем, заданы ли все необходимые параметры
    if len(args) < 2:
        # сообщение для ответа на успешный сброс значения макс. токенов
        answer_msg = "✅ *Ограничение на выходное кол-во токенов в ответе удалено. Максимальная длина ответа будет равна максимально-поддерживаемой длине ответа ИИ*"
        if (last_value := ai.config.get('max_tokens', None)):
            answer_msg = f"{answer_msg}\nПрошлое значение максимального количества выходных токенов в ответе было: `{last_value}`"
        ai.config["max_tokens"] = None
        ai.save_config()
        return await message.reply(answer_msg, parse_mode='Markdown')
    # Задаем новый префикс
    try:
        value = int(args[1])
        if value >= 32 and value <=32000:
            ai.config["max_tokens"] = value
            ai.save_config()
            await message.reply("`✅`", parse_mode='Markdown')
        else:
            message.reply("*Заданное число выходит за диапазон допустимых значений!*", parse_mode='Markdown')
    except:
        await message.reply("*Нужно указать число от* `32` *до* `32000`", parse_mode='Markdown')