import telebot
from telebot import types
import sqlite3
from datetime import datetime, timedelta

TOKEN = "9174898556:AAESLXlSiEuwdabS6HOwn9ACzv67GHPtY4o"
ADMIN_ID = 7643191802
CHANNEL1 = "@dev_y7_krd"
CHANNEL2 = "@y7_store7"

bot = telebot.TeleBot(TOKEN)

# دروستکردنی بنکەی داتای بۆت (Database)
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

# پشکنینی ئەندامبوونی کەناڵەکان (Force Subscribe)
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
    username = message.from_user.username or "بێ_یوزەرنێم"
    full_name = message.from_user.first_name
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, full_name, phone_number, expiry_date, joined_date) VALUES (?, ?, ?, ?, ?, ?)",
                   (user_id, username, full_name, "نەهێنراوە", "None", now_str))
    conn.commit()
    conn.close()

    check_and_route(message.chat.id, user_id, full_name)

def check_and_route(chat_id, user_id, full_name="بەکارهێنەر"):
    # 1. پشکنینی کەناڵەکان
    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("📢 کەناڵی یەکەم (@dev_y7_krd)", url="https://t.me/dev_y7_krd")
        btn2 = types.InlineKeyboardButton("📢 کەناڵی دووەم (@y7_store7)", url="https://t.me/y7_store7")
        btn_check = types.InlineKeyboardButton("✅ پشکنینی بەشداربوونم کرد", callback_data="check_sub")
        markup.add(btn1, btn2, btn_check)
        
        bot.send_message(chat_id, f"✨ سڵاو <b>{full_name}</b> گیان!\n\nبۆ دەستپێکردن و کارپێکردنی بۆتەکە، تکایە سەرەتا لە هەردوو کەناڵەکەمان ئەندام بە 👇", reply_markup=markup, parse_mode="HTML")
        return

    # 2. پشکنینی ناردنی کۆنتکت (Contact)
    user_data = get_user_data(user_id)
    phone = user_data[0] if user_data else "نەهێنراوە"

    if phone == "نەهێنراوە":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_contact = types.KeyboardButton("📱 ناردنی ژمارەی تەلەگرام (Contact)", request_contact=True)
        markup.add(btn_contact)
        bot.send_message(chat_id, "✅ بەشداربوونی کەناڵەکانت پشتڕاستکرایەوە!\n\n📱 ئێستا بۆ تێرکردنی مەرجەکانی تۆمارکردن و کردنەوەی بەشەکانی بۆت، تکایە ژمارەی تەلەگرامەکەت هاوبەش بکە 👇", reply_markup=markup)
        return

    show_main_menu(chat_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, "✅ بەشداربوونت پشتڕاستکرایەوە!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        check_and_route(call.message.chat.id, user_id, call.from_user.first_name)
    else:
        bot.answer_callback_query(call.id, "❌ تۆ هێشتا لە هەردوو کەناڵ نەبوویەتە ئەندام!", show_alert=True)

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

        bot.send_message(message.chat.id, "✅ ژمارەی تەلەگرامەکەت بە سەرکەوتوویی تۆمارکرا!\n\n🎉 ئێستا دەتوانیت بە تەواوی لە خزمەتگوزارییەکانی بۆت کەڵک وەربگریت.", parse_mode="Markdown")
        check_and_route(message.chat.id, user_id, message.from_user.first_name)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    text = message.text

    if not check_subscription(user_id) or get_user_data(user_id)[0] == "نەهێنراوە":
        check_and_route(message.chat.id, user_id, message.from_user.first_name)
        return

    if text == "👤 پڕۆفایل و پلانی من":
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT expiry_date, phone_number FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        expiry = row[0] if row else "None"
        phone = row[1] if row else "نەهێنراوە"
        
        is_active = False
        if expiry != "None":
            try:
                if datetime.strptime(expiry, "%Y-%m-%d") > datetime.now():
                    is_active = True
            except:
                pass

        status_text = "🟢 چالاک و بێگەرد" if is_active else "🔴 بەسەرچووە / پلانت نییە"

        profile_text = (
            f"👤 **زانیارییەکانی پڕۆفایلی تایبەتی تۆ:**\n\n"
            f"🆔 ئایدی: `{user_id}`\n"
            f"📌 یوزەرنێم: @{message.from_user.username or 'نییە'}\n"
            f"📱 ژمارەی تەلەگرام: `{phone}`\n"
            f"💎 دۆخی پلانی بەشداربوون: {status_text}\n"
            f"⏳ کاتی بەسەرچوونی پلان: `{expiry}`\n\n"
            f"🛒 بۆ کڕینی پلان یان نوێکردنەوەی، خێرا پەیوەندی بە @Y7_KRD بکە."
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
            no_plan_msg = (
                f"❌ **تۆ هیچ پلانێکی چالاکت نییە!**\n\n"
                f"بەڕێزەکەم، بۆ ئەوەی بتوانیت لەم بەشە کەڵک وەربگریت، پێویستە سەرەتا پلانت هەبێت. فەرموو بۆ کڕینی پلان پەیوەندی بە تیمەکەمان بکە:\n"
                f"🛒 @Y7_KRD"
            )
            bot.send_message(message.chat.id, no_plan_msg, parse_mode="Markdown")
            return

        msg = bot.send_message(message.chat.id, "🔍 تکایە یوزەرنێمەکەت بنووسە (بۆ نموونە: `Y7_KRD` یان `@Y7_KRD`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_search)

    elif text == "⚙️ بەڕێوەبەر (ئەی دەمین)" and user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_add = types.InlineKeyboardButton("➕ زیادکردن / نوێکردنەوەی پلان", callback_data="admin_add_sub")
        btn_zero = types.InlineKeyboardButton("🔄 سفرکردنەوەی پلان (بڕین)", callback_data="admin_zero_sub")
        btn_stats = types.InlineKeyboardButton("📊 ئامار و لیستی بەکارهێنەران", callback_data="admin_stats")
        markup.add(btn_add, btn_zero, btn_stats)
        bot.send_message(message.chat.id, "🛠 **پانێڵی تایبەتی بەڕێوەبەری (Admin Panel)**\nفەرموو بژاردەیەک هەڵبژێرە:", reply_markup=markup, parse_mode="Markdown")

def show_main_menu(chat_id, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_search = types.KeyboardButton("🔍 گەڕان و پشکنینی یوزەرنێم")
    btn_profile = types.KeyboardButton("👤 پڕۆفایل و پلانی من")
    markup.add(btn_search, btn_profile)

    if user_id == ADMIN_ID:
        btn_admin = types.KeyboardButton("⚙️ بەڕێوەبەر (ئەی دەمین)")
        markup.add(btn_admin)

    bot.send_message(chat_id, "🌟 فەرموو لە مێنۆیا سەرەکی بژاردەی دڵخوازی خۆت هەڵبژێرە:", reply_markup=markup)

def process_search(message):
    raw_query = message.text.strip()
    # دڵنیابوونەوە لەوەی ئایدی یوزەرنێم هەمیشە کاراکتەری @ لەخۆ بگرێت
    if raw_query.startswith("@"):
        query = raw_query
    else:
        query = f"@{raw_query}"

    user_id = message.from_user.id
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO searches (user_id, query, search_time) VALUES (?, ?, ?)", (user_id, query, now_str))
    conn.commit()
    conn.close()

    result_text = (
        f"🔍 **ئەنجامی پشکنینی پێشکەوتوو بۆ:** `{query}`\n\n"
        f"📌 **ناوی تۆمارکراو:** پشکنینی ناوەکی سەرکەوتوو بوو\n"
        f"🔗 **کەناڵ و گروپەکان:** دۆزراوەتەوە بە سەرکەوتوویی\n"
        f"📱 **جۆری ژمارەی تەلەگرام:** پارێزراو و چاودێریکراو\n"
        f"⏳ **مێژووی چالاکبوون:** مێژووی پاشەکەوتکراوی سیستم\n"
        f"💎 **دۆخی گشتی:** ئەکاونتەکە بێ کێشە و چالاکە\n\n"
        f"⚡️ دیزاین و پەرەپێدانی تایبەت لەلایەن: @Y7_KRD"
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
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE phone_number != 'نەهێنراوە'")
        total_contacts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM searches")
        total_searches = cursor.fetchone()[0]

        # هێنانی کۆتا بەکارهێنەرانی تۆمارکراو
        cursor.execute("SELECT user_id, username, full_name, phone_number, expiry_date FROM users ORDER BY rowid DESC LIMIT 15")
        users_rows = cursor.fetchall()
        conn.close()

        stats_summary = (
            f"📊 **ئامارە گشتییەکانی بۆت:**\n\n"
            f"👥 کۆی گشتی بەکارهێنەران: `{total_users}`\n"
            f"📱 کۆنتکت شاندراوەکان: `{total_contacts}`\n"
            f"🔍 کۆی گەڕانەکان: `{total_searches}`\n\n"
            f"📋 **لیستی بەکارهێنەرانی بۆت (کۆتا 15 کەس):**\n"
        )
        
        bot.answer_callback_query(call.id, "📊 ئامار و لیست دەرکەوت", show_alert=True)
        bot.send_message(call.message.chat.id, stats_summary, parse_mode="Markdown")

        # دروستکردنی لیسا بەکارهێنەران بۆ نیشاندان بە ئایدی و یوزەرنێم و ژمارە
        users_text = ""
        for u in users_rows:
            u_id, u_username, u_fullname, u_phone, u_expiry = u
            clean_username = f"@{u_username}" if u_username and u_username != "بێ_یوزەرنێم" else "بێ یوزەرنێم"
            users_text += f"👤 {u_fullname} | {clean_username}\n   🆔 ID: `{u_id}`\n   📱 ژمارە: `{u_phone}`\n\n"

        if users_text:
            bot.send_message(call.message.chat.id, users_text, parse_mode="Markdown")

    elif call.data == "admin_add_sub":
        msg = bot.send_message(call.message.chat.id, "👤 فەرموو **IDـی بەکارهێنەر** بنووسە بۆ زیادکردنی پلان:")
        bot.register_next_step_handler(msg, get_admin_user_id)

    elif call.data == "admin_zero_sub":
        msg = bot.send_message(call.message.chat.id, "🔄 فەرموو **IDـی بەکارهێنەر** بنووسە بۆ سفرکردنەوەی (بڕینی) پلانی وی:")
        bot.register_next_step_handler(msg, get_admin_zero_id)

def get_admin_user_id(message):
    try:
        target_id = int(message.text.strip())
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn6m = types.InlineKeyboardButton("6 مەهـ (مانگ)", callback_data=f"plan_6m_{target_id}")
        btn1y = types.InlineKeyboardButton("1 ساڵ", callback_data=f"plan_1y_{target_id}")
        markup.add(btn6m, btn1y)
        bot.send_message(message.chat.id, f"⏳ ماوەی پلان بۆ ئایدی `{target_id}` هەڵبژێرە:", reply_markup=markup, parse_mode="Markdown")
    except ValueError:
        bot.send_message(message.chat.id, "❌ ئایدی هەڵەیە! تکایە تەنها ژمارە بنووسە.")

def get_admin_zero_id(message):
    try:
        target_id = int(message.text.strip())
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET expiry_date = 'None' WHERE user_id = ?", (target_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ پلانی ئایدی `{target_id}` بە سەرکەوتوویی **سفرکراوەوە (بڕدرا)**!", parse_mode="Markdown")
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

    bot.answer_callback_query(call.id, "✅ پلان سەرکەوتووانە چالاک کرا!", show_alert=True)
    bot.send_message(call.message.chat.id, f"✅ پلان بۆ ئایدی `{target_id}` تاوەکو ڕێکەوتی **{expiry_str}** چالاک کرا!", parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot is running in Sorani...")
    bot.infinity_polling()
