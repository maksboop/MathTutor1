import aiosqlite

DB_NAME = 'math_tutor.db'


async def init_db():
    """Initializes the database and creates tables if they don't exist."""
    async with aiosqlite.connect(DB_NAME) as conn:
        # Create users table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT
            )
        ''')
        # Create messages table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT, -- 'user' or 'model'
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        await conn.commit()


async def add_user(user_id: int, username: str, first_name: str):
    """Adds a new user to the database if they don't already exist."""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if await cursor.fetchone() is None:
            await conn.execute("INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                               (user_id, username, first_name))
            await conn.commit()


async def add_message(user_id: int, role: str, content: str):
    """Adds a message to the user's chat history."""
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute("INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
                           (user_id, role, content))
        await conn.commit()


async def get_chat_history(user_id: int) -> list:
    """Retrieves the chat history for a user, formatted for Gemini."""
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row  # Позволяет обращаться к полям по имени, если нужно
        cursor = await conn.execute("SELECT role, content FROM messages WHERE user_id = ? ORDER BY timestamp ASC",
                                    (user_id,))
        history = await cursor.fetchall()

        # Format for Gemini API
        gemini_history = []
        for row in history:
            # aiosqlite возвращает объекты Row или кортежи, здесь мы берем по индексу или распаковываем
            role = row[0]
            content = row[1]
            gemini_history.append({"role": role, "parts": [content]})

        return gemini_history