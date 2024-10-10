import asyncio
# 
from datetime import datetime
# 
from aiogram import types
from aiogram.filters import CommandStart
from aiogram.filters.command import Command
# 
from modules import logger
from modules import funcs
from modules import routers_cmd
from modules import vision
from modules import decorators
# это импорт из __init__
from modules import bot, dp, router, tg_msg_max_len, bot_info, ai



# Обработчик команды /start
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(ai.send_message(message="Привет!", max_tokens=128))



# помощь
@router.message(Command('help'))
async def help(message: types.Message):
    help_text = """
*Помощь по командам:*
• /clear - _очистить память переписки_
• /trigs - _показать слова, на которые бот отзывается_
• `/addtrig` - _добавить слово-триггер. Пример:_ `/addtrig Ботан`
• `/deltrig` - _удалить указанное слово-триггер. Пример:_ `/deltrig Ботан`
• /cleartrigs - _удалить все слова-триггеры_
• /sys - _показать системный промпт_
• `/delsys` - _удалить системный промпт_
• `/setsys`- _задать системный промпт. Пример:_ `/setsys говори на японском`
• /pref - _показать префикс (роль)_
• `/delpref` - _удалить префикс_
• `/setpref` -  _задать префикс. Пример:_ `/setpref самурай Ямамото`
• `/maxtokens` - _задать макс. количество токенов, доступное для генерации ответа. От 32 до 32000. Пример:_ `/maxtokens 1024`. Если вызвать команду без числа, то кол-во токенов будет None, т.е. длина выходного сообщения не будет искусственно ограничена
    """
    await message.answer(help_text, parse_mode='Markdown')



# главный обработчик сообщений (текстовых сообщений для ИИ, не команд)
@router.message()
@decorators.lock_thread # декоратор для блокировки потока, чтобы не было ошибок в 
# последовательности обработки сообщений и обращения к файлам
@decorators.check_access
async def handle_group_messages(message: types.Message):
    # финальный текст сообщения
    final_text = ""
    img_info = None
    msg_info = f"@{message.from_user.username} : {datetime.now().strftime('%Y.%m.%d-%H:%M')}"
    # получаем текст сообщения, либо текст под картинкой (если что-то из этого есть вообще)
    msg_text = message.text or message.caption
    # если в сообщение есть изображение, выполняем обработку (переводим в текст)
    # в ТГ группа картинок (альбом) приходят в бота как отдельные сообщения
    if message.photo:
        # Сообщение содержит фото
        img_info = await vision.process_image_message(message=message, prompt=msg_text)
        final_text += f"показал изображение с таким содержанием: *{img_info}*" if img_info else ""
    # пробуем найти в сообщение изображение превьюшки
    elif message.entities:
        try:
            img_url = message.link_preview_options.get('url', None)
            img_info = await vision.process_image_message(img_url=img_url, prompt=msg_text)
            final_text += f"показал ссылку {img_url}, у которой превью-изображение с таким содержанием: *{img_info}*" if img_info else ""
            # удаляем ссылку на изображение превьюшки из сообщения
            if img_url and img_url in msg_text:
                msg_text = msg_text.replace(img_url, '')
        except Exception as error:
            pass

    # формируем финальный текст
    final_text = f"{final_text + (' и' if img_info and msg_text else '') + (' сказал: ' + msg_text if msg_text else '')}"

    if (re_type := await funcs.should_reply(bot=bot, message=message, text=msg_text.lower() if msg_text else '')):
        # Генерируем ответ AI
        if re_type == 'reply':
            response = ai.send_message(message = f'[{msg_info}] в ответ на сообщение [{message.reply_to_message.text}] {final_text}')
        elif re_type == True:
            response = ai.send_message(message = f'[{msg_info}]: {final_text}')
        else:
            return
        if response:
            # форматируем вывод
            response = funcs.format_response(response)
            # если сообщение слишком длинное, подрезаем
            if len(response) >= tg_msg_max_len:
                messages = funcs.split_message(message=response, max_length=tg_msg_max_len)
                await funcs.send_split_messages(bot=bot, message=message, messages=messages)
            else:
                await funcs.send_message(bot=bot, message=message, msg_text=response)
    else:
        # добавляем сообщение в историю, чтобы не терять часть контекста
        ai.add_message(text=f"[{msg_info}]: {final_text}" if final_text else None, role='user')

    # сохраняем в файл
    ai.save_history()



# Функция будет вызвана перед стартом поллинга!
async def on_startup():
    bot_information = await bot.get_me()
    bot_info.set_id(id=bot_information.id)
    bot_info.set_username(username=bot_information.username)
    logger.info(f"Bot started, ID: {bot_info.get_id()}, name: @{bot_info.get_username()}")













if __name__ == "__main__":
    dp.include_router(router)
    dp.startup.register(on_startup)
    asyncio.run(dp.start_polling(bot))
