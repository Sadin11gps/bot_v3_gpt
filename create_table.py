import psycopg2

DB_URL = "postgresql://rds_bot_user:X6j2MJD8Uim0mMm0AXFT6435fq9XIOI1@dpg-d42gp4v5r7bs73b0dgl0-a.oregon-postgres.render.com/rds_bot_db"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# পুরোনো টেবিল ড্রপ (যদি আগে তৈরি হয়ে থাকে)
cur.execute("DROP TABLE IF EXISTS users")
conn.commit()

# নতুন টেবিল তৈরি
cur.execute("""
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    name TEXT,
    clicked_button TEXT
)
""")
conn.commit()

cur.close()
conn.close()
print("Table created successfully!")
