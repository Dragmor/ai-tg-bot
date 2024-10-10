from functools import wraps
from aiogram import types
# 
from modules import lock


# для проверки доступа к боту
def check_access(func):
    @wraps(func)
    async def wrapper(trigger, *args, **kwargs):
        chat_id = trigger.chat.id # id чата, группы
        user_id = trigger.from_user.id # id юзера

        if type(trigger) == types.Message:
            print("ЭТО СООБЩЕНИЕ")

        elif type(trigger) == types.CallbackQuery:
            print("ЭТО КОЛБЕК")
            await trigger.answer()
        else:
            return None

        await func(trigger, *args, **kwargs)
    return wrapper


def lock_thread(func):
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        async with lock:
            await func(message, *args, **kwargs)
    return wrapper