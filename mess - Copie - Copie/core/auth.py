import mysql.connector
import hashlib
import secrets
from core.crypto_utils import generate_keys
from core.config import SALT, PEPPER

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="messagerie"
    )



def hash_password(password):
    return hashlib.sha256(SALT + password.encode() + PEPPER).hexdigest()

def register_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        return False

    password_hash = hash_password(password)

    public_key = generate_keys(username)

    try:
        cursor.execute("INSERT INTO users (username, password_hash, public_key) VALUES (%s, %s, %s)",
               (username, password_hash, public_key))

        conn.commit()
        return True
    except Exception as e:
        print("Erreur registre :", e)
        return False
    finally:
        cursor.close()
        conn.close()

def login_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return False

    password_hash = user[0]
    hashed_input = hash_password(password)

    return hashed_input == password_hash

def get_public_key(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT public_key FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def get_all_users():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    users = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return users

def save_message(sender, receiver, encrypted_for_receiver, encrypted_for_sender):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (sender, receiver, encrypted_for_receiver, encrypted_for_sender) VALUES (%s, %s, %s, %s)",
                   (sender, receiver, encrypted_for_receiver, encrypted_for_sender))
    conn.commit()
    cursor.close()
    conn.close()

def get_messages(user1, user2):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sender, receiver, encrypted_for_receiver, encrypted_for_sender
        FROM messages
        WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
        ORDER BY timestamp ASC
    """, (user1, user2, user2, user1))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return messages

def get_user_language(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT preferred_language FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else "fr"

def set_user_language(username, lang_code):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET preferred_language = %s WHERE username = %s", (lang_code, username))
    conn.commit()
    cursor.close()
    conn.close()
