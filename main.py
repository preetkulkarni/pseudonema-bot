import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from contextlib import asynccontextmanager

from scout_agent import run_scout

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ptb_application = None

async def start_week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a topic.\nUsage: /start_week Cybersecurity")
        return

    topic = " ".join(context.args)
    await update.message.reply_text(f"🕵️ Scout Agent activated for: *{topic}*\nScanning RSS & Reddit...", parse_mode="Markdown")

    try:
        count = await run_scout(topic)
        await update.message.reply_text(f"✅ Mission Complete.\nFound {count} articles and saved them to the database.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error during scouting: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ptb_application
    if TOKEN:
        ptb_application = Application.builder().token(TOKEN).build()
    
        ptb_application.add_handler(CommandHandler("start_week", start_week_command))
        await ptb_application.initialize()
        await ptb_application.start()
    yield
    if ptb_application:
        await ptb_application.stop()
        await ptb_application.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, ptb_application.bot)
        await ptb_application.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error"}