import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from openrouter_api import query_openrouter
from config import BOT_TOKEN, WEBHOOK_URL
from languagetool_api import check_text_with_languagetool

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

MODES = {
    "teacher": "You are a friendly English teacher. Correct grammar mistakes, explain difficult words when asked, and encourage the student to speak more.",
    "grammar": "You are an English grammar checker. Whenever the user sends a sentence, reply with a corrected version and a brief explanation of the corrections.",
    "translator": "You are a professional English-Russian translator. Translate the user's messages from English to Russian while preserving the tone and context.",
    "examiner": "You are an English proficiency exam instructor. Ask the user speaking or writing test questions, evaluate the answers, and provide feedback with a score from 1 to 10.",
    "companion": "You are a friendly English-speaking companion. Hold casual conversations in English. Keep replies short and light. Avoid teaching unless asked."
}

user_prompts = {}

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start"), KeyboardButton(text="/help")],
        [KeyboardButton(text="/choosemode"), KeyboardButton(text="/currentmode")],
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Hello! I'm your AI English companion bot.\n\nChoose a command from the menu below or type your message.",
        reply_markup=main_menu
    )

@dp.message(Command("help"))
async def help_handler(message: Message):
    help_text = (
        "📖 *Справка по боту:*\n\n"
        "Я — твой AI-помощник для изучения английского. Вот что я умею:\n\n"
        "🗨️ /choosemode — выбрать режим общения:\n"
        "• *Teacher* — исправляет ошибки, даёт пояснения.\n"
        "• *Grammar* — проверяет грамматику.\n"
        "• *Translator* — переводит на русский.\n"
        "• *Examiner* — экзаменатор.\n"
        "• *Companion* — лёгкий разговорный собеседник.\n\n"
        "🎛️ /currentmode — узнать текущий режим.\n"
        "📑 /help — показать эту справку.\n"
        "🎛️ /start — перезапуск."
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("choosemode"))
async def choose_mode_inline(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=mode.title(), callback_data=f"setmode:{mode}")]
            for mode in MODES.keys()
        ]
    )
    await message.answer("📲 Choose a mode:", reply_markup=keyboard)

@dp.callback_query()
async def process_callback(callback: CallbackQuery):
    if callback.data.startswith("setmode:"):
        mode = callback.data.split(":")[1]
        user_prompts[callback.message.chat.id] = MODES[mode]
        await callback.message.answer(f"✅ Mode set to: {mode}", reply_markup=main_menu)
        await callback.answer()

@dp.message(Command("setmode"))
async def set_mode(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❗ Please specify a mode. Use /choosemode.", reply_markup=main_menu)
        return
    mode = parts[1].strip().lower()
    if mode in MODES:
        user_prompts[message.chat.id] = MODES[mode]
        await message.answer(f"✅ Mode set to: {mode}", reply_markup=main_menu)
    else:
        await message.answer("❌ Unknown mode.", reply_markup=main_menu)

@dp.message(Command("currentmode"))
async def current_mode(message: Message):
    current_prompt = user_prompts.get(message.chat.id)
    if current_prompt:
        current_mode_name = next((k for k, v in MODES.items() if v == current_prompt), "Custom / Unknown")
        await message.answer(f"ℹ️ Current mode: {current_mode_name}", reply_markup=main_menu)
    else:
        await message.answer("ℹ️ Current mode: teacher (default)", reply_markup=main_menu)

@dp.message()
async def ai_handler(message: Message):
    prompt = user_prompts.get(message.chat.id, MODES["teacher"])

    # LanguageTool автопроверка
    result = await check_text_with_languagetool(message.text)
    matches = result.get("matches", [])

    if matches:
        response_text = "✏️ *Language check:*\n\n"
        for match in matches:
            offset = match["offset"]
            length = match["length"]
            error = message.text[offset:offset+length]
            message_txt = match["message"]
            replacement = match["replacements"][0]["value"] if match["replacements"] else "—"
            response_text += f"🔸 *{error}* → *{replacement}*\n_{message_txt}_\n\n"
        await message.answer(response_text, parse_mode="Markdown")

    # OpenRouter ответ
    await message.answer("Thinking... 🤔")
    reply = await query_openrouter(message.text, prompt)
    await message.answer(reply, reply_markup=main_menu)

# 📌 Keep-alive функция
async def keep_alive():
    import aiohttp
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(WEBHOOK_URL.replace("/webhook", "/")) as response:
                    print("Keep-alive ping:", response.status)
        except Exception as e:
            print("Keep-alive error:", e)
        await asyncio.sleep(300)  # каждые 5 минут

# 📌 Webhook setup
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set at {WEBHOOK_URL}")
    asyncio.create_task(keep_alive())

# 📌 Запуск aiohttp
app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
setup_application(app, dp, bot=bot, on_startup=on_startup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))





