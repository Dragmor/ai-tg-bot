import os
import asyncio
from aiogram import Bot, Dispatcher, Router
# 
from modules.bot_info_class import BOT_INFO
from modules.ai_class import AI




# сколько максимум символов может быть в сообщении в ТГ (если в ответе больше - ответ будет разбит на сообщения)
tg_msg_max_len = 4096 

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
router = Router()
# сюда данные будут записаны после запуска, в bot.py -> on_startup()
bot_info = BOT_INFO()


ai = AI(api_key=os.getenv("API_KEY"), 
    history_file=os.path.join("cfg", os.getenv("MEMORY_FILE")),
    config_file=os.path.join("cfg", os.getenv("CONFIG_FILE")))