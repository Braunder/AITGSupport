import asyncio
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
import os
from dotenv import load_dotenv

# try to import RAG if available
try:
    from rag import RAG
except Exception:
    RAG = None

# Загружаем переменные окружения
load_dotenv()

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")
USE_RAG = os.getenv("USE_RAG", "0") in ("1", "true", "True")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Инициализация БД
def init_db():
    conn = sqlite3.connect('bot_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        response TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        satisfaction INTEGER
    )''')
    conn.commit()
    conn.close()

# Системный промпт для ассистента поддержки
SYSTEM_PROMPT = """Ты — AI-ассистент первой линии поддержки контакт-центра. 
Твоя задача: помочь пользователю, собрать информацию о проблеме и, если нужно, 
перевести на оператора. Отвечай кратко, по делу, на русском языке."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я AI-ассистент поддержки.\\n"
        "Опишите вашу проблему, и я постараюсь помочь."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # Если RAG включена и модуль доступен — используем retrieval-augmented generation
    if USE_RAG and RAG is not None:
        rag = context.bot_data.get("rag")
        if rag is None:
            rag = RAG()
            context.bot_data["rag"] = rag

        gen = rag.generate_answer(user_message, top_k=3, system_prompt=SYSTEM_PROMPT)
        ai_response = gen.get("answer") if isinstance(gen, dict) else str(gen)
    else:
        # Получаем ответ от OpenAI
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=300
        )
        ai_response = response.choices[0].message.content
    
    # Сохраняем в БД
    conn = sqlite3.connect('bot_history.db')
    c = conn.cursor()
    c.execute('INSERT INTO conversations (user_id, message, response) VALUES (?, ?, ?)',
              (user_id, user_message, ai_response))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(ai_response)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('bot_history.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*), AVG(satisfaction) FROM conversations')
    total, avg_sat = c.fetchone()
    conn.close()
    
    await update.message.reply_text(
        f"📊 Статистика:\\n"
        f"Всего диалогов: {total}\\n"
        f"Средняя оценка: {avg_sat or 'N/A'}"
    )

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
