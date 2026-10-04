import os

import telebot
from dotenv import load_dotenv

from app.agent import ask_agent, clear_memory


load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError(
        "TELEGRAM_BOT_TOKEN не найден в .env"
    )


bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=["start"])
def start_command(message):
    bot.reply_to(
        message,
        "Привет! 👋\n\n"
        "Я персональный AI-ассистент с памятью на Pinecone.\n\n"
        "Я умею:\n"
        "🐱 рассказывать факты о кошках;\n"
        "🌤 показывать текущую погоду;\n"
        "🧠 помнить твои сообщения;\n"
        "🐶 анализировать изображения собак.\n\n"
        "Попробуй спросить меня о погоде, "
        "попросить рассказать факт о кошках "
        "или отправить фотографию собаки.\n\n"
        "Команды:\n"
        "/start — запустить бота\n"
        "/help — показать помощь\n"
        "/clear — очистить твою память",
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.reply_to(
        message,
        "🤖 Что я умею:\n\n"
        "🌤 Погода\n"
        "Например: «Какая сейчас погода в Москве?»\n\n"
        "🐱 Факты о кошках\n"
        "Например: «Расскажи интересный факт о кошках»\n\n"
        "🧠 Память\n"
        "Я помню твои сообщения и свои ответы. "
        "Память разделена по пользователям.\n\n"
        "🐶 Изображения собак\n"
        "Отправь мне фотографию собаки, "
        "и я попробую определить её породу, "
        "окрас и внешний вид.\n\n"
        "/clear — очистить твою память",
    )


@bot.message_handler(commands=["clear"])
def clear_command(message):
    try:
        clear_memory(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
        )

        bot.reply_to(
            message,
            "🧹 Твоя память очищена.",
        )

    except Exception as error:
        print(f"Ошибка очистки памяти: {error}")

        bot.reply_to(
            message,
            "Не удалось очистить память.",
        )


@bot.message_handler(content_types=["photo"])
def handle_photo_message(message):
    image_path = None

    try:
        bot.send_chat_action(
            message.chat.id,
            "typing",
        )

        photo = message.photo[-1]

        file_info = bot.get_file(
            photo.file_id
        )

        downloaded_file = bot.download_file(
            file_info.file_path
        )

        image_path = os.path.join(
            "/tmp",
            f"telegram_dog_{message.message_id}.jpg",
        )

        with open(image_path, "wb") as file:
            file.write(downloaded_file)

        caption = message.caption or ""

        response = ask_agent(
            caption,
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            image_path=image_path,
        )

        bot.reply_to(
            message,
            response,
        )

    except Exception as error:
        print(
            f"Ошибка анализа изображения: {error}"
        )

        bot.reply_to(
            message,
            "Не удалось проанализировать изображение. "
            "Попробуй отправить другую фотографию.",
        )

    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


@bot.message_handler(
    content_types=["text"],
    func=lambda message: True,
)
def handle_text_message(message):
    user_text = message.text

    if not user_text or not user_text.strip():
        return

    try:
        bot.send_chat_action(
            message.chat.id,
            "typing",
        )

        response = ask_agent(
            user_text,
            user_id=message.from_user.id,
            chat_id=message.chat.id,
        )

        bot.reply_to(
            message,
            response,
        )

    except Exception as error:
        print(
            f"Ошибка обработки сообщения: {error}"
        )

        bot.reply_to(
            message,
            "Произошла ошибка при обработке сообщения. "
            "Попробуй ещё раз.",
        )


if __name__ == "__main__":
    print("Telegram-бот запущен...")
    bot.infinity_polling()