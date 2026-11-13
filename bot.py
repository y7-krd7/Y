import telebot
from telebot import types
import sqlite3
from datetime import datetime, timedelta

TOKEN = "9174898556:AAESLXlSiEuwdabS6HOwn9ACzv67GHPtY4o"
ADMIN_ID = 7643191802
CHANNEL1 = "@dev_y7_krd"
CHANNEL2 = "@y7_store7"

bot = telebot.TeleBot(TOKEN)

# دروستکرنا بنکەیا داتایێ ب جدولێن پێویست
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone_number TEXT,
            expiry_date TEXT,
            joined_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT,
            search_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# پشکنینا بەشداربوونا کەناڵان
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

# وەرگرتنا زانیاریێن بەکارهێنەری ژ داتایێ
def get_user_data(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT phone_number, expiry_date FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "بێ یوزەرنێم"
    full_name = message.from_user.first_name
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, full_name, phone_number, expiry_date, joined_date) VALUES (?, ?, ?, ?, ?, ?)",
                   (user_id, username, full_name, "نەهاتیە شاندن", "None", now_str))
    conn.commit()
    conn.close()

    check_and_route(message.chat.id, user_id, full_name)

# سیستەمێ پشکنینا مەجلبوری (Join + Contact)
def check_and_route(chat_id, user_id, full_name="بەکارهێنەر"):
    # 1. پشکنینا کەناڵان
    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("📢 کەناڵی یەکەم (@dev_y7_krd)", url="https://t.me/dev_y7_krd")
        btn2 = types.InlineKeyboardButton("📢 کەناڵی دووەم (@y7_store7)", url="https://t.me/y7_store7")
        btn_check = types.InlineKeyboardButton("✅ پشکنینی بەشداربوونم کرد", callback_data="check_sub")
        markup.add(btn1, btn2, btn_check)
        
        bot.send_message(chat_id, f"سڵاو <b>{full_name}</b> عزیز!\n\nبۆ دەستپێکردنی بۆتەکە، تکایە سەرەتا لە هەردوو کەناڵەکەمان ئەندام بە 👇", reply_markup=markup, parse_mode="HTML")
        return

    # 2. پشکنینا شاندنا ژمارەی تەلەگرام (Contact)
    user_data = get_user_data(user_id)
    phone = user_data[0] if user_data else "نەهاتیە شاندن"

    if phone == "نەهاتیە شاندن":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_contact = types.KeyboardButton("📱 شاندنی ژمارەی تەلەگرام (Contact)", request_contact=True)
        markup.add(btn_contact)
        bot.send_message(chat_id, "✅ بەشداربوونی کەناڵەکانت پشتڕاستکرایەوە!\n\n📱 ئێستا بۆ تەواوکردنی تۆمارکردن و کارپێکردنی بۆتەکە، تکایە ژمارەی تەلەگرامەکەت (Contact) هاوبەش بکە 👇", reply_markup=markup)
        return

    # ئەگەر هەردوو مەرج بڕین، مێنۆیا سەرەکی نیشان بدە
    show_main_menu(chat_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, "✅ بەشداربوونت پشتڕاستکرایەوە!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        check_and_route(call.message.chat.id, user_id, call.from_user.first_name)
    else:
        bot.answer_callback_query(call.id, "❌ تو هێشتا لە هەردوو کەناڵ نەبوویەتە ئەندام!", show_alert=True)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    if message.contact:
        phone = message.contact.phone_number
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET phone_number = ? WHERE user_id = ?", (f"+{phone}", user_id))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, "✅ ژمارەی تەلەگرامەکەت بە سەرکەوتوویی تۆمارکرا!\n\n🎉 ئێستا دەتوانیت تەواوی فەرمان و بەشەکانی بۆتەکە بەکاربهێنیت.", parse_mode="Markdown")
        check_and_route(message.chat.id, user_id, message.from_user.first_name)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    text = message.text

    # پاراستن: ئەگەر هێشتا مەرج نەبڕین، ڕێگری لێ بکە و بگەڕێنە سەر مەرجی سەرەکی
    if not check_subscription(user_id) or get_user_data(user_id)[0] == "نەهاتیە شاندن":
        check_and_route(message.chat.id, user_id, message.from_user.first_name)
        return

    if text == "👤 پڕۆفایل و پلانی من":
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT expiry_date, phone_number FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        expiry = row[0] if row else "None"
        phone = row[1] if row else "نەهاتیە شاندن"
        status_text = "🟢 چالاکە" if expiry != "None" and datetime.strptime(expiry, "%Y-%m-%d") > datetime.now() else "🔴 بەسەرچووە / نییە"

        profile_text = (
            f"👤 **زانیارییەکانی پڕۆفایلی تۆ:**\n\n"
            f"🆔 ئایدی: `{user_id}`\n"
            f"📌 یوزەرنێم: @{message.from_user.username or 'نییە'}\n"
            f"📱 ژمارەی تەلەگرام: `{phone}`\n"
            f"💎 پلانی بەشداربوون: {status_text}\n"
            f"⏳ بەسەرچوونی پلان: `{expiry}`\n\n"
            f"🛒 بۆ کڕینی پلان پەیوەندی بە @Y7_KRD بکە."
        )
        bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")

    elif text == "🔍 گەڕان و پشکنینی یوزەرنێم":
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT expiry_date FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        has_access = (user_id == ADMIN_ID) or (row and row[0] != "None" and datetime.strptime(row[0], "%Y-%m-%d") > datetime.now())

        if not has_access:
            bot.send_message(message.chat.id, "❌ **پلان نییە یان بەسەرچووە!**\n\nتکایە بۆ کڕینی پلان پەیوەندی بە @Y7_KRD بکە.", parse_mode="Markdown")
            return

        msg = bot.send_message(message.chat.id, "🔍 تکایە یوزەرنێمی تەلەگرام (بێ @) بنووسە بۆ پشکنینی گشتگیر:")
        bot.register_next_step_handler(msg, process_search)

    elif text == "⚙️ بەڕێوەبەر (ئەی دەمین)" and user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_add = types.InlineKeyboardButton("➕ زیادکرن / نووکرنا اشتراکێ", callback_data="admin_add_sub")
        btn_zero = types.InlineKeyboardButton("🔄 صفرکرنا پلانێ (ڕاگرتن / 0)", callback_data="admin_zero_sub")
        btn_stats = types.InlineKeyboardButton("📊 ئامارێن بۆتی و بەکارهێنەران", callback_data="admin_stats")
        markup.add(btn_add, btn_zero, btn_stats)
        bot.send_message(message.chat.id, "🛠 **پانێڵی بەڕێوەبەری (Admin Panel)**\nفەرموو بژاردەیەک هەڵبژێرە:", reply_markup=markup, parse_mode="Markdown")

def show_main_menu(chat_id, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_search = types.KeyboardButton("🔍 گەڕان و پشکنینی یوزەرنێم")
    btn_profile = types.KeyboardButton("👤 پڕۆفایل و پلانی من")
    markup.add(btn_search, btn_profile)

    if user_id == ADMIN_ID:
        btn_admin = types.KeyboardButton("⚙️ بەڕێوەبەر (ئەی دەمین)")
        markup.add(btn_admin)

    bot.send_message(chat_id, "🌟 فەرموو مێنۆیا سەرەکی یەکێک لە بژاردەکان هەڵبژێرە:", reply_markup=markup)

def process_search(message):
    query = message.text.replace("@", "").strip()
    user_id = message.from_user.id
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO searches (user_id, query, search_time) VALUES (?, ?, ?)", (user_id, query, now_str))
    conn.commit()
    conn.close()

    result_text = (
        f"🔎 **ئەنجامی پشکنینی گشتگیر بۆ یوزەرنێم:** `@{query}`\n\n"
        f"📌 **ناڤێ دانای سەر ئەکاونتی:** شیکاریا زیرەک و تۆمارێن گشتی\n"
        f"🔗 **کەناڵ و گروپێن پەیوەندیدار:** پشکنینی ناڤخۆیی سەرکەوتوو بوو\n"
        f"📱 **جۆرێ ژمارە و تەلەگرام:** پشکنینی نهێنی سەرکەوتوو بوو\n"
        f"⏳ **مێژووی دەستپێکرنا ئەکاونتی:** تەخمینی زەمنی دیارە\n"
        f"📊 **دۆخی چالاکی:** ئەکاونت سەلامەت و ڤەکرییە\n\n"
        f"⚡️ پەرەپێدابوون و دروستکراوە لەلایەن تیمەکەمان: @Y7_KRD"
    )
    bot.send_message(message.chat.id, result_text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["admin_add_sub", "admin_zero_sub", "admin_stats"])
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    if call.data == "admin_stats":
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE phone_number != 'نەهاتیە شاندن'")
        total_contacts = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM searches")
        total_searches = cursor.fetchone()[0]
        conn.close()

        stats_text = (
            f"📊 **ئامارێن گشتی یێن بۆتی:**\n\n"
            f"👥 کۆی گشتی بەکارهێنەران: `{total_users}`\n"
            f"📱 ئەو کەسێن کۆنتکت شاندین: `{total_contacts}`\n"
            f"🔍 کۆی گشتی گەڕانێن هاتینە ئەنجامدان: `{total_searches}`\n\n"
            f"⚙️ بەڕێوەبەر: @Y7_KRD"
        )
        bot.answer_callback_query(call.id, "📊 ئامار هاتنە نیشاندان", show_alert=True)
        bot.send_message(call.message.chat.id, stats_text, parse_mode="Markdown")

    elif call.data == "admin_add_sub":
        msg = bot.send_message(call.message.chat.id, "👤 فەرموو **IDـی بەکارهێنەر** بنووسە بۆ زیادکرنا اشتراکێ:")
        bot.register_next_step_handler(msg, get_admin_user_id)

    elif call.data == "admin_zero_sub":
        msg = bot.send_message(call.message.chat.id, "🔄 فەرموو **IDـی بەکارهێنەر** بنووسە بۆ صفرکرنا (ڕاگرتن / 0) پلانێ وی:")
        bot.register_next_step_handler(msg, get_admin_zero_id)

def get_admin_user_id(message):
    try:
        target_id = int(message.text.strip())
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn6m = types.InlineKeyboardButton("6 مەهـ (مانگ)", callback_data=f"plan_6m_{target_id}")
        btn1y = types.InlineKeyboardButton("1 ساڵ", callback_data=f"plan_1y_{target_id}")
        markup.add(btn6m, btn1y)
        bot.send_message(message.chat.id, f"⏳ ماوەی اشتراک بۆ ئایدی `{target_id}` هەڵبژێرە:", reply_markup=markup, parse_mode="Markdown")
    except ValueError:
        bot.send_message(message.chat.id, "❌ ئایدی هەڵەیە! تەنها ژمارە بنووسە.")

def get_admin_zero_id(message):
    try:
        target_id = int(message.text.strip())
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET expiry_date = 'None' WHERE user_id = ?", (target_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ پلانا ئایدی `{target_id}` ب سەرکەوتوویی هاتە **صفرکرن (ڕاگرتن / 0)**!", parse_mode="Markdown")
    except ValueError:
        bot.send_message(message.chat.id, "❌ ئایدی هەڵەیە!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("plan_"))
def set_plan_duration(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    parts = call.data.split("_")
    duration_type = parts[1]
    target_id = int(parts[2])

    now = datetime.now()
    if duration_type == "6m":
        expiry_date = now + timedelta(days=180)
    else:
        expiry_date = now + timedelta(days=365)
    
    expiry_str = expiry_date.strftime("%Y-%m-%d")

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET expiry_date = ? WHERE user_id = ?", (expiry_str, target_id))
    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, "✅ اشتراک چالاک کرا!", show_alert=True)
    bot.send_message(call.message.chat.id, f"✅ اشتراک بۆ ئایدی `{target_id}` تاوەکو ڕێکەوتی **{expiry_str}** هاتە فعالکرن!", parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
