from utils import db

# এখানে তোমার টেলিগ্রাম ID বসাও (যা শুধু এডমিন হবে)
ADMIN_ID = 7702378694

# এডমিন কমান্ড চেক
def is_admin(message):
    return message.from_user.id == ADMIN_ID

# ইউজার তালিকা দেখা
def view_users(bot, message):
    if is_admin(message):
        db.cur.execute("SELECT telegram_id, name, clicked_button FROM users")
        rows = db.cur.fetchall()
        if rows:
            msg = "Users in Database:\n"
            for row in rows:
                msg += f"ID: {row[0]}, Name: {row[1]}, Button: {row[2]}\n"
        else:
            msg = "Database is empty!"
        bot.send_message(message.chat.id, msg)
    else:
        bot.send_message(message.chat.id, "You are not admin!")

# ইউজার ডিলিট করা
def delete_user(bot, message, telegram_id):
    if is_admin(message):
        db.cur.execute("DELETE FROM users WHERE telegram_id=%s", (telegram_id,))
        db.conn.commit()
        bot.send_message(message.chat.id, f"User {telegram_id} deleted successfully!")
    else:
        bot.send_message(message.chat.id, "You are not admin!")
