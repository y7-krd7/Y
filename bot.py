import telebot
from telebot import types
import sqlite3
from datetime import datetime, timedelta

TOKEN = "9174898556:AAESLXlSiEuwdabS6HOwn9ACzv67GHPtY4o"
ADMIN_ID = 7643191802
CHANNEL1 = "@dev_y7_krd"
CHANNEL2 = "@y7_store7"

bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            expiry_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def check_subscription(user_id):
    try:
        member1 = bot.get_chat_member(CHANNEL1, user_id)
        member2 = bot.get_chat_member(CHANNEL2, user_id)
        not_allowed_statuses = ['left', 'kicked', 'banned']
        if member1.status in not_allowed_statuses or member2.status in not_allowed_statuses:
            return False
        return True
    except:
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "بێ یوزەرنێم"
    full_name = message.from_user.first_name

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, full_name, expiry_date) VALUES (?, ?, ?, ?)",
                   (user_id, username, full_name, "None"))
    conn.commit()
    conn.close()

    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("📢 کەناڵی یەکەم (@dev_y7_krd)", url="https://t.me/dev_y7_krd")
        btn2 = types.InlineKeyboardButton("📢 کەناڵی دووەم (@y7_store7)", url="https://t.me/y7_store7")
        btn_check = types.InlineKeyboardButton("✅ پشکنینی بەشداربوونم کرد", callback_data="check_sub")
        markup.add(btn1, btn2, btn_check)
        
        bot.send_message(message.chat.id, f"سڵاو <b>{full_name}</b>!\n\nبۆ بەکارهێنانی بۆتەکە، تکایە سەرەتا لە کەناڵەکان ئەندام بە 👇", reply_markup=markup, parse_mode="HTML")
        return

    show_main_menu(message.chat.id, user_id)

def show_main_menu(chat_id, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_search = types.KeyboardButton("🔍 گەڕان و پشکنینی یوزەرنێم")
    btn_phone = types.KeyboardButton("📱 پشکنینی ژمارەی من (Contact)")
    btn_profile = types.KeyboardButton("👤 پڕۆفایل و پلانی من")
    markup.add(btn_search, btn_phone, btn_profile)

    if user_id == ADMIN_ID:
        btn_admin = types.KeyboardButton("⚙️ بەڕێوەبەر (ئەی دەمین)")
        markup.add(btn_admin)

    bot.send_message(chat_id, "🌟 فەرموو یەکێک لە بژاردەکانی خوارەوە هەڵبژێرە:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, "✅ بەشداربوونت پشتڕاستکرایەوە!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.message.chat.id, user_id)
    else:
        bot.answer_callback_query(call.id, "❌ تو هێشتا لە کەناڵەکان نەبوویەتە ئەندام!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    text = message.text

    if not check_subscription(user_id):
        bot.send_message(message.chat.id, "❌ تکایە سەرەتا لە کەناڵەکان ببە ئەندام و /start بنووسە.")
        return

    if text == "👤 پڕۆفایل و پلانی من":
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT expiry_date FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        expiry = row[0] if row else "None"
        status_text = "🟢 چالاکە" if expiry != "None" and datetime.strptime(expiry, "%Y-%m-%d") > datetime.now() else "🔴 بەسەرچووە / نییە"

        profile_text = (
            f"👤 **پڕۆفایلی تۆ:**\n\n"
            f"🆔 ئایدی: `{user_id}`\n"
            f"📌 یوزەرنێم: @{message.from_user.username or 'نییە'}\n"
            f"💎 پلانی بەشداربوون: {status_text}\n"
            f"⏳ بەسەرچوونی پلان: `{expiry}`\n\n"
            f"🛒 بۆ کڕینی پلان پەیوەندی بە @Y7_KRD بکە."
        )
        bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")

    elif text == "📱 پشکنینی ژمارەی من (Contact)":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_contact = types.KeyboardButton("share 📱 پشکنینی ژمارەی من", request_contact=True)
        btn_back = types.KeyboardButton("🔙 گەڕانەوە")
        markup.add(btn_contact, btn_back)
        bot.send_message(message.chat.id, "بۆ پشکنینی ژمارا خۆیا ڕاستەقینە، ل خوارێ دوگمەیا (پشکنینی ژمارەی من) لێدێ 👇", reply_markup=markup)

    elif text == "🔙 گەڕانەوە":
        show_main_menu(message.chat.id, user_id)

    elif message.contact:
        phone = message.contact.phone_number
        bot.send_message(message.chat.id, f"✅ ژمارا تەلەگراما تە هاتە دیتن:\n\n📱 ژمارە: `+{phone}`\n🌍 کەنارا وەڵاتی: دیارە\n\n⚡️ دروستکراوە لەلایەن تیمەکەمان: @Y7_KRD", parse_mode="Markdown")
        show_main_menu(message.chat.id, user_id)

    elif text == "🔍 گەڕان و پشکنینی یوزەرنێم":
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT expiry_date FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        has_access = (user_id == ADMIN_ID) or (row and row[0] != "None" and datetime.strptime(row[0], "%Y-%m-%d") > datetime.now())

        if not has_access:
            bot.send_message(message.chat.id, "❌ **پلان نییە یان بەسەرچووە!**\n\nتکایە پەیوەندی بە @Y7_KRD بکە بۆ کڕینی پلان.", parse_mode="Markdown")
            return

        msg = bot.send_message(message.chat.id, "🔍 تکایە یوزەرنێمی تەلەگرام (بێ @) بنووسە بۆ پشکنین:")
        bot.register_next_step_handler(msg, process_search)

    elif text == "⚙️ بەڕێوەبەر (ئەی دەمین)" and user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_add = types.InlineKeyboardButton("➕ زیادکردنی اشتراک", callback_data="admin_add_sub")
        btn_stats = types.InlineKeyboardButton("📊 ئاماری بۆت", callback_data="admin_stats")
        markup.add(btn_add, btn_stats)
        bot.send_message(message.chat.id, "🛠 **پانێڵی بەڕێوەبەری (Admin Panel)**", reply_markup=markup, parse_mode="Markdown")

def process_search(message):
    query = message.text.replace("@", "").strip()
    result_text = (
        f"🔎 **ئەنجامی پشکنینی یوزەرنێم:** `@{query}`\n\n"
        f"📱 **جۆرێ ئەکاونتی:** پشکنینا پێشوەختە نیشان ددەت کە ئەکاونت چالاکە.\n"
        f"🔒 **تایبەتمەندی:** ژمارە ڤەشارتەیە (Hidden Number Privacy).\n"
        f"👥 **چەڤدێریا کەناڵ و گروپ:** پشکنین سەرکەوتوو بوو.\n\n"
        f"⚡️ دروستکراوە لەلایەن تیمەکەمان: @Y7_KRD"
    )
    bot.send_message(message.chat.id, result_text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["admin_add_sub", "admin_stats"])
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        return
    if call.data == "admin_stats":
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        bot.answer_callback_query(call.id, f"📊 کۆی گشتی بەکارهێنەران: {count}", show_alert=True)
    elif call.data == "admin_add_sub":
        msg = bot.send_message(call.message.chat.id, "👤 فەرموو **IDـی بەکارهێنەر** بنووسە:")
        bot.register_next_step_handler(msg, get_admin_user_id)

def get_admin_user_id(message):
    try:
        target_id = int(message.text.strip())
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn6m = types.InlineKeyboardButton("6 مەهـ", callback_data=f"plan_6m_{target_id}")
        btn1y = types.InlineKeyboardButton("1 ساڵ", callback_data=f"plan_1y_{target_id}")
        markup.add(btn6m, btn1y)
        bot.send_message(message.chat.id, f"⏳ ماوەی اشتراک بۆ ئایدی `{target_id}` هەڵبژێرە:", reply_markup=markup, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ ئایدی هەڵەیە!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("plan_"))
def set_plan_duration(call):
    if call.from_user.id != ADMIN_ID:
        return
    parts = call.data.split("_")
    duration_type = parts[1]
    target_id = int(parts[2])
    expiry_date = datetime.now() + timedelta(days=180 if duration_type == "6m" else 365)
    expiry_str = expiry_date.strftime("%Y-%m-%d")

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET expiry_date = ? WHERE user_id = ?", (expiry_str, target_id))
    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, "✅ اشتراک چالاک کرا!", show_alert=True)
    bot.send_message(call.message.chat.id, f"✅ اشتراک بۆ ئایدی `{target_id}` تاوەکو ڕێکەوتی **{expiry_str}** چالاک کرا!", parse_mode="Markdown")

if __name__ == "__main__":
    bot.infinity_polling()
