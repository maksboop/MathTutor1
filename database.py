import sqlite3
import json

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    with sqlite3.connect('math_tutor.db') as conn:
        cursor = conn.cursor()
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT
            )
        ''')
        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT, -- 'user' or 'model'
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        conn.commit()

def add_user(user_id: int, username: str, first_name: str):
    """Adds a new user to the database if they don't already exist."""
    with sqlite3.connect('math_tutor.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                           (user_id, username, first_name))
            conn.commit()

def add_message(user_id: int, role: str, content: str):
    """Adds a message to the user's chat history."""
    with sqlite3.connect('math_tutor.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
                       (user_id, role, content))
        conn.commit()

def get_chat_history(user_id: int) -> list:
    """Retrieves the chat history for a user, formatted for Gemini."""
    with sqlite3.connect('math_tutor.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role, content FROM messages WHERE user_id = ? ORDER BY timestamp ASC", (user_id,))
        history = cursor.fetchall()
        
        # Format for Gemini API
        gemini_history = []
        for role, content in history:
            gemini_history.append({"role": role, "parts": [content]})
            
        return gemini_history
