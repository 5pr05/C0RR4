import asyncio
import threading

import telebot
from telebot import types

import config
import corra
import light_control

bot = telebot.TeleBot(config.TOKEN)
user_chat_id = None


def send_tg_status(message):
    if user_chat_id:
        bot.send_message(user_chat_id, message)
    print(f"[LOG] {message}")


@bot.message_handler(commands=["start"])
def welcome(message):
    global user_chat_id
    user_chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Desk Lamp💡"))
    bot.send_message(message.chat.id, "/ [ ^_^]_##", reply_markup=markup)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    global user_chat_id

    if user_chat_id is None:
        bot.send_message(message.chat.id, "i can't see u.. help me, type /start.")
        return

    if message.chat.type == "private":
        match message.text:
            case "Desk Lamp💡":
                corra.send_status("lamp_toggle", tg_session=True)
                asyncio.run_coroutine_threadsafe(
                    light_control.control_desk_lamp("-toggle"), async_loop
                )


async_loop = asyncio.new_event_loop()


def run_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


async_thread = threading.Thread(target=run_async_loop, args=(async_loop,), daemon=True)
async_thread.start()


def start_bot():
    bot.infinity_polling()
