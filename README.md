# Telegram Bot with AI Support Assistant

> A first-line support Telegram bot with OpenAI API integration, optional RAG (Retrieval-Augmented Generation), and conversation analytics. Built with an AI assistant for dialog architecture and system prompt design.

---

## What It Does

The bot receives messages from users in Telegram, processes them via LLM (OpenAI GPT), and responds as a first-line support assistant. It supports two operating modes: direct LLM call and RAG with knowledge base search.

### Features

| Feature | Description |
|---------|-------------|
| `/start` | Welcome message and instructions |
| Text messages | Query processing via OpenAI API |
| RAG mode | Search for relevant documents before generating a response |
| SQLite storage | Saving history of all conversations |
| `/stats` | Statistics: number of conversations, average rating |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Telegram API | python-telegram-bot v20+ |
| LLM | OpenAI GPT-4o-mini |
| Embeddings (RAG) | sentence-transformers (all-MiniLM-L6-v2) |
| Database | SQLite |
| Configuration | python-dotenv |

---

## Installation

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/Braunder/AITGSupport.git
cd AITGSupport
pip install python-telegram-bot openai sentence-transformers python-dotenv numpy
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
BOT_TOKEN=your_telegram_bot_token_from_BotFather
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
USE_RAG=0          # 1 to enable RAG mode
```

### 3. Run

```bash
python bot.py
```

The bot will start polling and respond to messages in Telegram.

---

## Architecture

```
User (Telegram)
    ↓
python-telegram-bot (Application)
    ↓
handle_message()
    ├── RAG mode (USE_RAG=1)
    │   ├── retrieve() — embedding-based search
    │   └── generate_answer() — LLM + context
    └── Direct mode (USE_RAG=0)
        └── openai.ChatCompletion.create()
    ↓
SQLite (bot_history.db)
    ↓
Response to user
```

---

## Project Structure

```
.
├── bot.py              # Main bot script
├── rag.py              # RAG module (retrieval + generation)
├── .env                # Environment variables (do not commit!)
├── bot_history.db      # SQLite DB (created automatically)
└── README.md           # This file
```

---

## Modules

### `bot.py`

Main script. Initializes the DB, sets up Telegram handlers, and starts polling.

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `init_db()` | Creates `conversations` table in SQLite |
| `start()` | Handler for `/start` command |
| `handle_message()` | Main handler for text messages |
| `stats()` | Handler for `/stats` — analytics |
| `main()` | Entry point — assembles Application and starts polling |

**`conversations` Table Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `user_id` | INTEGER | Telegram user ID |
| `message` | TEXT | User's question |
| `response` | TEXT | Bot's answer |
| `timestamp` | DATETIME | Conversation time (DEFAULT CURRENT_TIMESTAMP) |
| `satisfaction` | INTEGER | User rating 1–5 (NULL by default) |

### `rag.py`

Retrieval-Augmented Generation module. Adds context from the knowledge base before generating a response.

**`RAG` Class:**

| Method | Description |
|--------|-------------|
| `__init__(embedding_model)` | Loads SentenceTransformer, checks OPENAI_API_KEY |
| `add_documents(docs)` | Indexes documents: computes embeddings |
| `retrieve(query, top_k)` | Searches top-k relevant documents by cosine similarity |
| `generate_answer(query, top_k, system_prompt)` | Retrieval + LLM generation with context |

**Document format for `add_documents`:**

```python
docs = [
    {"id": "doc1", "text": "Instructions for resetting password...", "meta": {"category": "auth"}},
    {"id": "doc2", "text": "What to do if VPN is not working...", "meta": {"category": "network"}}
]
```

---

## Operating Modes

### Mode 1: Direct LLM (USE_RAG=0)

Good for quick start. Each message is sent to OpenAI API without additional context.

**Pros:** Simplicity, no knowledge base preparation required  
**Cons:** No access to internal company documentation

### Mode 2: RAG (USE_RAG=1)

Before generating a response, the bot searches for relevant documents in the knowledge base and includes them in the prompt.

**Pros:** Answers are based on up-to-date documentation, fewer hallucinations  
**Cons:** Requires preparation and indexing of documents

**RAG initialization example in code:**

```python
from rag import RAG

rag = RAG(embedding_model="all-MiniLM-L6-v2")
rag.add_documents([
    {"id": "faq_1", "text": "To reset your password, click 'Forgot password'..."},
    {"id": "faq_2", "text": "If the internet is not working, check the router indicator..."}
])
```

---

## Example Conversation

```
User: /start
Bot: Hello! I'm an AI support assistant.
     Describe your issue, and I'll try to help.

User: My internet is not working
Bot: Got it. Let's figure it out. Tell me: is the router indicator on?
      And can you access other websites?

User: The indicator is on, but websites won't open
Bot: Try rebooting the router (unplug it for 30 seconds).
      If that doesn't help — I'll escalate you to a technician.

User: /stats
Bot: 📊 Statistics:
      Total conversations: 42
      Average rating: 4.2
```

---

## AI Tools in Development

| Stage | How AI Was Used |
|-------|-----------------|
| Architecture design | AI suggested the structure: handlers → LLM/RAG → SQLite → response |
| System prompt | AI generated the base SYSTEM_PROMPT for the support assistant |
| RAG module | AI helped implement cosine similarity via numpy dot product |
| Error handling | AI suggested graceful fallback when OPENAI_API_KEY is missing |
| DB schema | AI designed the schema with a satisfaction field for future analytics |

---

## Development Time

| Stage | Time |
|-------|------|
| Bot skeleton (handlers, polling) | 30 min |
| OpenAI API integration | 20 min |
| RAG module (retrieval + generation) | 25 min |
| SQLite storage and `/stats` command | 20 min |
| Testing and debugging | 25 min |
| **Total** | **~2 hours** |

---

## Possible Improvements

- [ ] Inline buttons for conversation rating (1–5 stars)
- [ ] Escalation to a human operator on low-confidence LLM responses
- [ ] Integration with Confluence/Notion for auto-updating the knowledge base
- [ ] Webhook mode instead of polling (for production)
- [ ] Docker containerization
- [ ] Monitoring: latency, error rate, satisfaction metrics

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Token from @BotFather |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_MODEL` | No | LLM model (default: `gpt-4o-mini`) |
| `USE_RAG` | No | Enable RAG: `1` or `true` (default: `0`) |
