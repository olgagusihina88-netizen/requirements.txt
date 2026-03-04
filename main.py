# main.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Получаем ключи из переменных окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# Простая память для обратной связи
user_feedback = {}

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Напиши, что ищешь и в каком городе.\n"
        "Например: 'купить лопату в Тюмени'"
    )

# --- Обработка сообщений ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id

    await update.message.reply_text("Ищу варианты и анализирую отзывы... ⏳")

    # --- Для MVP: список ссылок вручную ---
    sample_items = [
        {
            "name": "Лопата стандартная",
            "price": "350 ₽",
            "rating": "4.8",
            "reviews": ["Очень хорошая лопата, держит металл.", "Удобная ручка, не ломается."],
            "url": "https://vk.com/shop_lopata",
            "image": "https://example.com/lopata1.jpg"
        },
        {
            "name": "Лопата усиленная",
            "price": "400 ₽",
            "rating": "4.5",
            "reviews": ["Крепкая, но тяжеловата.", "Доставка быстрая, товар хороший."],
            "url": "https://vk.com/shop_lopata2",
            "image": "https://example.com/lopata2.jpg"
        },
        {
            "name": "Лопата легкая",
            "price": "300 ₽",
            "rating": "4.2",
            "reviews": ["Легкая, но чуть слабый металл.", "Отлично для дачи."],
            "url": "https://vk.com/shop_lopata3",
            "image": "https://example.com/lopata3.jpg"
        }
    ]

    # --- Формируем промт для OpenAI ---
    prompt = "Анализируй эти товары по отзывам и цене, отсортируй 3 лучших:\n"
    for item in sample_items:
        prompt += f"\nНазвание: {item['name']}, Цена: {item['price']}, Рейтинг: {item['rating']}, Отзывы: {item['reviews']}, Ссылка: {item['url']}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        best_items = response.choices[0].message.content
    except Exception as e:
        best_items = "Ошибка при анализе данных."

    # --- Отправка пользователю ---
    await update.message.reply_text(f"Вот лучшие варианты по вашему запросу:\n{best_items}")

    # Кнопка для обратной связи
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Оставить отзыв", callback_data=f"feedback_{user_id}")]])
    await update.message.reply_text("Вы выбрали один из вариантов? Хотите оставить отзыв?", reply_markup=keyboard)

# --- Обработка нажатия кнопки ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await query.edit_message_text("Напишите пару слов о вашем выборе:")
    user_feedback[user_id] = ""  # создаем запись

# --- Обработка текста обратной связи ---
async def feedback_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_feedback:
        user_feedback[user_id] = update.message.text
        await update.message.reply_text("Спасибо! Ваш отзыв сохранен.")
    else:
        # если сообщение обычное — обрабатываем как поиск
        await handle_message(update, context)

# --- Запуск бота ---
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), feedback_text))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
app.add_handler(MessageHandler(filters.UpdateType.CALLBACK_QUERY, button_callback))

print("Бот запущен...")
app.run_polling()
