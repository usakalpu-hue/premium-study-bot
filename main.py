import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from threading import Thread
from flask import Flask
import asyncio

# --- CONFIGURATION ---
# Render के Environment Variables से डेटा उठाएगा
TOKEN = os.getenv("8643810259:AAFOGKJ4kAT93Mofdx-DLvmgutI_7bc4dTU")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Default Settings (शुरुआत के लिए)
settings = {
    "prices": {"basic": "99", "premium": "199", "lifetime": "499", "podcast": "149"},
    "links": {"basic": "none", "premium": "none", "lifetime": "none", "podcast": "none", "demo": "none"},
    "upi": "yourname@upi"
}

# --- FLASK SERVER (For Render) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"
def run(): app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))

# --- BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = settings["prices"]
    text = (
        "💎 **Premium Study Material & Podcast Store** 💎\n\n"
        "नमस्ते! सबसे सस्ता और बेहतरीन स्टडी मटेरियल यहाँ उपलब्ध है।\n\n"
        "👇 **अपना पैक चुनें:**"
    )
    keyboard = [
        [InlineKeyboardButton(f"📘 Basic - ₹{p['basic']}", callback_data="buy_basic"),
         InlineKeyboardButton(f"💎 Premium - ₹{p['premium']}", callback_data="buy_premium")],
        [InlineKeyboardButton(f"🎙 Podcast - ₹{p['podcast']}", callback_data="buy_podcast")],
        [InlineKeyboardButton(f"👑 Lifetime Access - ₹{p['lifetime']}", callback_data="buy_lifetime")],
        [InlineKeyboardButton("📺 View Demo", callback_data="buy_demo")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = (
        "👑 **Admin Control**\n\n"
        "💰 **Set Price:** `/setprice pack price`\n"
        "🔗 **Set Link:** `/setlink pack url`\n"
        "💳 **Set UPI:** `/setupi id`\n\n"
        "Packs: `basic, premium, lifetime, podcast, demo`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def update_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    cmd = update.message.text.split()
    try:
        if cmd[0] == "/setprice":
            settings["prices"][cmd[1]] = cmd[2]
            await update.message.reply_text(f"✅ {cmd[1]} Price updated to ₹{cmd[2]}")
        elif cmd[0] == "/setlink":
            settings["links"][cmd[1]] = cmd[2]
            await update.message.reply_text(f"✅ {cmd[1]} Link updated!")
        elif cmd[0] == "/setupi":
            settings["upi"] = cmd[1]
            await update.message.reply_text(f"✅ UPI updated to {cmd[1]}")
    except:
        await update.message.reply_text("❌ Error! Check format.")

async def handle_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split("_")[1]
    await query.answer()

    if data == "demo":
        await query.message.reply_text(f"📺 **Demo Link:** {settings['links']['demo']}")
        return

    context.user_data['pack'] = data
    price = settings["prices"][data]
    upi = settings["upi"]
    
    caption = (
        f"🎯 **Selected:** {data.upper()}\n"
        f"💰 **Amount:** ₹{price}\n"
        f"💳 **UPI:** `{upi}`\n\n"
        "1. ऊपर दिए UPI पर पेमेंट करें।\n"
        "2. पेमेंट का **Screenshot** यहाँ भेजें।"
    )
    try:
        await query.message.reply_photo(photo=open("qr.jpg", "rb"), caption=caption, parse_mode="Markdown")
    except:
        await query.message.reply_text(caption, parse_mode="Markdown")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pack = context.user_data.get('pack', 'Unknown')
    
    await update.message.reply_text("⏳ Admin आपकी पेमेंट चेक कर रहे हैं...")

    btn = [[InlineKeyboardButton("✅ Approve", callback_data=f"app_{user.id}_{pack}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user.id}_{pack}")]]
    
    admin_msg = await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"📩 **New Payment**\n👤 User: {user.first_name}\n🆔 ID: `{user.id}`\n📦 Pack: {pack.upper()}",
        reply_markup=InlineKeyboardMarkup(btn),
        parse_mode="Markdown"
    )
    # 10 मिनट बाद एडमिन मैसेज डिलीट करने के लिए
    context.job_queue.run_once(delete_msg, 600, data=(ADMIN_ID, admin_msg.message_id))

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action, uid, pack = query.data.split("_")
    
    if action == "app":
        link = settings["links"].get(pack, "Link not set")
        await context.bot.send_message(uid, f"✅ **Payment Approved!**\n\nपैक: {pack.upper()}\nलिंक: {link}")
        await query.edit_message_caption("✅ Approved and Link Sent!")
    else:
        await context.bot.send_message(uid, "❌ **Payment Rejected!** सही स्क्रीनशॉट भेजें।")
        await query.edit_message_caption("❌ Rejected!")

async def delete_msg(context: ContextTypes.DEFAULT_TYPE):
    chat_id, msg_id = context.job.data
    try: await context.bot.delete_message(chat_id, msg_id)
    except: pass

if __name__ == '__main__':
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("admin", admin_panel))
    bot.add_handler(CommandHandler(["setprice", "setlink", "setupi"], update_settings))
    bot.add_handler(CallbackQueryHandler(admin_action, pattern="^(app_|rej_)"))
    bot.add_handler(CallbackQueryHandler(handle_click, pattern="^buy_"))
    bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    bot.run_polling()
