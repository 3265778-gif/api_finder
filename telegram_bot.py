"""
telegram_bot.py — Telegram-інтерфейс для API Finder Bot
========================================================
Запуск: python telegram_bot.py

Команди в Telegram:
  /start  — вітання
  /help   — довідка
  /batch  — запустити пакетний пошук
  [назва АФІ] — пошук конкретного АФІ
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_IDS    = set(
    int(x) for x in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",") if x.strip()
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def check_telegram_installed():
    try:
        import telegram
        return True
    except ImportError:
        return False


def run_bot():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не знайдено в .env")
        return

    if not check_telegram_installed():
        print("❌ python-telegram-bot не встановлено")
        print("   Встановіть: pip install python-telegram-bot>=21.0")
        return

    from telegram import Update
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        filters, ContextTypes
    )
    from agent import build_agent

    agent = build_agent()

    def is_allowed(user_id: int) -> bool:
        return not ALLOWED_IDS or user_id in ALLOWED_IDS

    async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update.effective_user.id):
            return
        await update.message.reply_text(
            "💊 *API Finder Bot — Pharmasel*\n\n"
            "Надішліть назву АФІ або CAS-номер для пошуку.\n\n"
            "Приклади:\n"
            "• `metformin`\n"
            "• `CAS 657-24-9`\n"
            "• `Знайди постачальників vancomycin для ін'єкцій`\n\n"
            "/help — детальніша довідка",
            parse_mode="Markdown"
        )

    async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update.effective_user.id):
            return
        await update.message.reply_text(
            "📖 *Довідка API Finder Bot*\n\n"
            "*Джерела даних:*\n"
            "• PubChem — CAS, формула, маса\n"
            "• ChEMBL — фарм. клас, механізм\n"
            "• FDA NDC — реєстраційний статус\n"
            "• Web search — постачальники, ціни\n\n"
            "*Приклади запитів:*\n"
            "`imipenem` — повний звіт\n"
            "`CAS 74-79-3` — пошук за CAS\n"
            "`Порівняй meropenem та imipenem` — порівняння\n"
            "`Антибіотики для BFS ін'єкцій` — клас АФІ\n",
            parse_mode="Markdown"
        )

    async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ Доступ заборонено.")
            return

        query = update.message.text.strip()
        thinking_msg = await update.message.reply_text(
            f"⏳ Шукаю інформацію про `{query}`...\n"
            "_Це може зайняти 20-40 секунд_",
            parse_mode="Markdown"
        )

        try:
            result = agent.invoke({"input": query})
            output = result.get("output", "Відповідь відсутня")

            # Telegram має ліміт 4096 символів
            if len(output) > 4000:
                parts = [output[i:i+4000] for i in range(0, len(output), 4000)]
                await thinking_msg.delete()
                for part in parts:
                    await update.message.reply_text(part)
            else:
                await thinking_msg.edit_text(output)

        except Exception as e:
            logger.error(f"Agent error: {e}")
            await thinking_msg.edit_text(f"❌ Помилка: {e}")

    # Збірка бота
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Telegram bot запущено...")
    print("🤖 Telegram bot запущено! Ctrl+C для зупинки.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_bot()
