import psycopg2

DB_URL = "postgresql://rds_bot_user:X6j2MJD8Uim0mMm0AXFT6435fq9XIOI1@dpg-d42gp4v5r7bs73b0dgl0-a.oregon-postgres.render.com/rds_bot_db"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

def create_table():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        name TEXT,
        clicked_button TEXT
    )
    """)
    conn.commit()

def add_user(telegram_id, name):
    cur.execute("INSERT INTO users (telegram_id, name) VALUES (%s, %s) ON CONFLICT (telegram_id) DO NOTHING", (telegram_id, name))
    conn.commit()

def update_button(telegram_id, button):
    cur.execute("UPDATE users SET clicked_button=%s WHERE telegram_id=%s", (button, telegram_id))
    conn.commit()
