import os
import sqlite3
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message
)

# ----------------- زانیاریەکانی پەنڵ و بۆت -----------------
# API_ID و API_HASH لە Environment Variables وەردەگیرێن بۆ سەلامەتی زیاتر
API_ID = int(os.getenv("API_ID", "34584240"))
API_HASH = os.getenv("API_HASH", "eba4f8333cba5f9697a1d20779d4d6e9")
BOT_TOKEN = "9133255052:AAEy4V0ce3jb5CT0_xDLH4c1blBVvF9541o"
ADMIN_ID = 7643191802

app = Client(
    "y7_vip_advanced_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ----------------- دروستکردنی داتابەیسی پێشکەوتوو -----------------
def init_db():
    conn = sqlite3.connect("bot_advanced_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            plan_status INTEGER DEFAULT 0,  -- 0: نییە، 6: ٦ مانگ، 12: ١ ساڵ
            plan_expiry TEXT DEFAULT 'نەبوو'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS family_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_name TEXT,
            age INTEGER,
            occupation TEXT,
            grandfather_name TEXT,
            great_grandfather_name TEXT,
            extra_info TEXT,
            file_id TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect("bot_advanced_database.db")

# ----------------- مۆنیۆی سەرەکی -----------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 پروفایلی من", callback_data="profile")],
        [InlineKeyboardButton("💎 کڕینی پلان", callback_data="buy_plan")],
        [InlineKeyboardButton("🔍 گەڕان و زانیاری خێزانی", callback_data="search_menu")],
        [InlineKeyboardButton("⚡️ پەنێڵی ئەمین", callback_data="admin_panel")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 گەڕانەوە بۆ سەرەکی", callback_data="back_home")]
    ])

# ----------------- دەستپێک (START) -----------------
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user = message.from_user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user.id, user.username or "نییە", user.first_name)
        )
        conn.commit()
    conn.close()

    welcome_text = (
        f"✨ **بەخێر هاتیت بۆ بۆتی تایبەتی و پێشکەوتووی TEAM Y7!**\n\n"
        f"👤 **نازناو (Nickname):** {user.first_name}\n"
        f"🔗 **یوزەرنەم:** @{user.username if user.username else 'نییە'}\n"
        f"🆔 **ئایدی (ID):** `{user.id}`\n\n"
        f"بۆ ئەنجامدانی هەر کارێک تکایە یەکێک لە دوگمەکانی خوارەوە هەڵبژێرە 👇"
    )
    
    await message.reply_text(welcome_text, reply_markup=main_menu())

# ----------------- بەڕێوەبردنی کلیکەکان (Callbacks) -----------------
@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user = callback_query.from_user
    conn = get_db()
    cursor = conn.cursor()

    if data == "profile":
        cursor.execute("SELECT plan_status FROM users WHERE user_id = ?", (user.id,))
        row = cursor.fetchone()
        plan = "❌ پلانت نییە"
        if row and row[0] == 6:
            plan = "💎 پلانی ٦ مانگی فعالە"
        elif row and row[0] == 12:
            plan = "💎 پلانی ١ ساڵی فعالە"

        text = (
            f"👤 **زانیاری پروفایلی تە:**\n\n"
            f"• ناوی تە: {user.first_name}\n"
            f"• یوزەرنەم: @{user.username if user.username else 'نییە'}\n"
            f"• ئایدی (ID): `{user.id}`\n"
            f"• جۆری پلان: {plan}"
        )
        await callback_query.message.edit_text(text, reply_markup=back_menu())

    elif data == "buy_plan":
        text = (
            "💎 **بۆ کڕینی پلان و بەدەستهێنانی تایبەتمەندییە مەزنەکان:**\n\n"
            "تکایە سەردانی ئەم کەسە بکە بۆ مەبەستی کڕین و چالاککردنی پلانەکەت:\n"
            "👉 @y7_krd\n\n"
            "پاش پەیوەندیکردن، ئەمین خێرای بۆتەکەت بۆ چالاک دەکات!"
        )
        await callback_query.message.edit_text(text, reply_markup=back_menu())

    elif data == "search_menu":
        cursor.execute("SELECT plan_status FROM users WHERE user_id = ?", (user.id,))
        row = cursor.fetchone()
        if not row or row[0] == 0:
            if user.id != ADMIN_ID:
                await callback_query.answer(
                    "❌ هەڵە! تا پلانت نەبێت ناتوانیت بەشی گەڕان بەکاربهێنیت. تکایە پلان بکڕە لە @y7_krd",
                    show_alert=True
                )
                conn.close()
                return

        text = (
            "🔍 **بەشی گەڕان و زانیاری خێزانی (3 قۆڵی):**\n\n"
            "تکایە ناوی ئەو کەسە بنووسە کە دەتەوێت گەڕانی بۆ ئەنجام بدەین (بۆ نموونە: ناوی سیانی یان نیکی نامە).\n"
            "بۆت بە شێوازێکی زۆر پێشکەوتووە تەمەن، پیشە، ناوی باپیران و زانیاری خێزانی پیشان دەدات!"
        )
        await callback_query.message.edit_text(text, reply_markup=back_menu())

    elif data.startswith("fam_det_"):
        record_id = int(data.split("_")[2])
        cursor.execute("SELECT target_name, age, occupation, grandfather_name, great_grandfather_name, extra_info FROM family_records WHERE id = ?", (record_id,))
        rec = cursor.fetchone()
        if rec:
            name, age, occ, gf, ggf, extra = rec
            detail_text = (
                f"📋 **زانیاری و وردەکاری تەواوی خێزانی:**\n\n"
                f"• **ناوی تەواو:** {name}\n"
                f"• **تەمەن:** {age} ساڵ\n"
                f"• **پیشە:** {occ}\n"
                f"• **ناوی باپیر:** {gf}\n"
                f"• **ناوی باپیری باپیر (3 قۆڵی):** {ggf}\n"
                f"• **زانیاری زیاتر:** {extra}\n\n"
                f"✨ *شێوازی هێڵەکان (Line Spacing): 1.5 ڕێکخراوە.*"
            )
            await callback_query.message.edit_text(detail_text, reply_markup=back_menu())
        else:
            await callback_query.answer("❌ زانیاری نەدۆزرایەوە!", show_alert=True)

    elif data == "admin_panel":
        if user.id != ADMIN_ID:
            await callback_query.answer("❌ لێبوردە، ئەم پەنێڵە تەنها بۆ بەڕێوەبەرە!", show_alert=True)
            conn.close()
            return

        text = (
            "⚡️ **پەنێڵی تایبەتی بەڕێوەبەر (Admin Panel):**\n\n"
            "بۆ چالاککردن یان سفرکردنەوەی پلان بە ڕێگەی ئایدی، فەرماندەکانی خوارەوە بەکاربهێنە:\n\n"
            "• بۆ پێدانی پلانی ٦ مانگ:\n`/setplan [USER_ID] 6`\n\n"
            "• بۆ پێدانی پلانی ١ ساڵ:\n`/setplan [USER_ID] 12`\n\n"
            "• بۆ سفرکردنەوەی پلان (کەردنە صفر):\n`/setplan [USER_ID] 0`\n\n"
            "• بۆ زیادکردنی تۆماری خێزانی نوێ:\n`/addfamily [Name] | [Age] | [Occupation] | [Grandfather] | [Great-Grandfather] | [Extra Info]`"
        )
        await callback_query.message.edit_text(text, reply_markup=back_menu())

    elif data == "back_home":
        await callback_query.message.edit_text(
            f"✨ **بەخێر هاتیتەوە بۆ بۆتی سەرەکی!**\n\nبژاردەیەک هەڵبژێرە 👇",
            reply_markup=main_menu()
        )
    
    conn.close()

# ----------------- فەرمانی ئەمین بۆ زیادکردنی زانیاری خێزانی -----------------
@app.on_message(filters.command("addfamily") & filters.private)
async def add_family_command(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        content = message.text.split(" ", 1)[1]
        parts = [p.strip() for p in content.split("|")]
        if len(parts) < 6:
            await message.reply_text("❌ شێوازی هەڵە!\nنموونە:\n`/addfamily أحمد سنان | 35 | مهندس | محمد | سعيد | خێزانێکی بەڕێز`")
            return
        
        name, age, occ, gf, ggf, extra = parts[0], int(parts[1]), parts[2], parts[3], parts[4], parts[5]
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO family_records (target_name, age, occupation, grandfather_name, great_grandfather_name, extra_info) VALUES (?, ?, ?, ?, ?, ?)",
            (name, age, occ, gf, ggf, extra)
        )
        conn.commit()
        conn.close()
        
        await message.reply_text("✅ زانیاری خێزانی بە سەرکەوتوویی لە داتابەیسدا تۆمارکرا!")
    except Exception as e:
        await message.reply_text(f"❌ هەڵە لە تێکردنی زانیاری: {str(e)}")

# ----------------- کۆدی فەرمانی ئەمین بۆ بەڕێوەبردنی پلانەکان -----------------
@app.on_message(filters.command("setplan") & filters.private)
async def set_plan_command(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.command
    if len(args) != 3:
        await message.reply_text(
            "❌ شێوازی هەڵە!\nبەکاربهێنە بەم شێوەیە:\n`/setplan [user_id] [6/12/0]`",
            quote=True
        )
        return

    try:
        target_id = int(args[1])
        plan_val = int(args[2])
    except ValueError:
        await message.reply_text("❌ تکایە ئایدی و پلانی دروست بنووسە (ژمارە بن).", quote=True)
        return

    if plan_val not in [0, 6, 12]:
        await message.reply_text("❌ پلانی هەڵە! تەنها دەتوانیت 6 یان 12 یان 0 دابنێیت.", quote=True)
        return

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET plan_status = ? WHERE user_id = ?", (plan_val, target_id))
    conn.commit()
    conn.close()

    await message.reply_text(f"✅ سەرکەوتوو بوو! پلانی بەکارهێنەر `{target_id}` ڕێکخرا بۆ: **{plan_val}**", quote=True)

# ----------------- وەرگرتنی فایل، پشکنینی قەبارە (> 5GB)، و گەڕانی پێشکەوتووی خێزانی -----------------
@app.on_message(filters.private & (filters.document | filters.video | filters.text))
async def handle_uploads_and_search(client: Client, message: Message):
    # پشکنینی قەبارەی فایل (نابێت لە 5 گێگابایت زیاتر بێت)
    if message.document or message.video:
        media = message.document or message.video
        file_size_gb = media.file_size / (1024 * 1024 * 1024)
        if file_size_gb > 5.0:
            await message.reply_text("❌ لێبوردە، قەبارەی ئەم فایلە لە ٥ گێگابایت زیاترە و قەدەغەیە!", quote=True)
            return
        
        if message.document:
            await message.reply_text("📥 فایلەکەت بە سەرکەوتوویی لە سیستمدا تۆمار کرا!", quote=True)
        return

    # ئەگەر تێکست بوو وەک گەڕانی ناو داتابەیس بەکار دێت
    if message.text and not message.text.startswith("/"):
        query_text = message.text.strip()
        conn = get_db()
        cursor = conn.cursor()
        
        # گەڕان بە دوای ناوەکاندا
        cursor.execute("SELECT id, target_name, age, occupation FROM family_records WHERE target_name LIKE ?", (f"%{query_text}%",))
        results = cursor.fetchall()
        conn.close()

        if results:
            keyboard = []
            for r in results:
                rec_id, name, age, occ = r
                # دروستکردنی دوگمەی هێڵکاری (Line Keyboard) بۆ هەر ئەنجامێک
                btn_text = f"👤 {name} | تەمەن: {age} | پیشە: {occ}"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"fam_det_{rec_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 گەڕانەوە بۆ سەرەکی", callback_data="back_home")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text(
                f"🔍 **ئەنجامی گەڕان بۆ:** `{query_text}`\n"
                f"تکایە بۆ بینینی وردەکاری و تەمەن و زانیاری خێزانی، کلیک لەسەر ناوەکە بکە 👇\n\n"
                f"*(Line Spacing 1.5 رێکخراوە بۆ جوانی)*",
                reply_markup=reply_markup,
                quote=True
            )
        else:
            await message.reply_text(
                f"❌ هیچ زانیارییەک نەدۆزرایەوە بۆ ناوی: **{query_text}**\n\n"
                f"تکایە دڵنیابە لەوەی ناوەکە بە دروستی نووسیوە.",
                reply_markup=back_menu(),
                quote=True
            )

# ----------------- دەستپێکردنی بۆت -----------------
if __name__ == "__main__":
    print("Bot is starting with VIP setup...")
    app.run()
