from functools import wraps
from aiogram import types
# 
from modules import lock

# декоратор для проверки доступа (сообщения)
def check_access(func):
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        user_id = message.from_user.id
        if user_id not in users_manager.users_data:
            await message.answer(MESSAGES['access']['access_deny'])
            return
        await func(message, *args, **kwargs)
    return wrapper

# декоратор для проверки доступа (клавиатура)
def check_access_callback(func):
    @wraps(func)
    async def wrapper(call: types.CallbackQuery, *args, **kwargs):
        user_id = call.from_user.id
        if user_id not in users_manager.users_data:
            await call.answer()
            await call.message.answer(MESSAGES['access']['access_deny'])
            return
        await func(call, *args, **kwargs)
    return wrapper

def lock_thread(func):
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        async with lock:
            await func(message, *args, **kwargs)
    return wrapper