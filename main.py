import os
from threading import Thread
from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

UPI_ID = "Q562574548@ybl"

DEMO_LINK = "https://t.me/+cwlEHvWpayc4YmYx"

PACK_LINKS = {
    "basic": "https://t.me/+aLCwjZzWns9hMDY1",
    "premium": "https://t.me/+aLCwjZzWns9hMDY1",
    "lifetime": "https://t.me/+aLCwjZzWns9hMDY1"
}

PRICES = {
    "basic": "99",
    "premium": "199",
    "lifetime": "499"
}

# =========================
# FLASK SERVER
# =========================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running"

def run():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

def keep_alive():
    Thread(target=run).start()

# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "💎 PREMIUM MAAL 💦\n\n"
        "📚 Premium Study Material\n"
        "⚡ Instant Delivery\n"
        "💳 UPI Payment Available\n\n"
        "👇 Select Your Pack"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                f"📘 BASIC ₹{PRICES['basic']}",
                callback_data="buy_basic"
            )
        ],
        [
            InlineKeyboardButton(
                f"💎 PREMIUM ₹{PRICES['premium']}",
                callback_data="buy_premium"
            )
        ],
        [
            InlineKeyboardButton(
                f"👑 LIFETIME ₹{PRICES['lifetime']}",
                callback_data="buy_lifetime"
            )
        ],
        [
            InlineKeyboardButton(
                "🎥 DEMO",
                url=DEMO_LINK
            )
        ]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# BUTTON HANDLER
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    data = query.data

    await query.answer()

    # BUY BUTTON

    if data.startswith("buy_"):

        pack = data.split("_")[1]

        context.user_data["pack"] = pack

        caption = (
            f"💳 PAYMENT DETAILS\n\n"
            f"📦 Pack: {pack.upper()}\n"
            f"💰 Price: ₹{PRICES[pack]}\n"
            f"🆔 UPI ID:\n`{UPI_ID}`\n\n"
            f"📸 Payment screenshot send karo."
        )

        try:

            with open("qr.jpg", "rb") as qr:

                await query.message.reply_photo(
                    photo=qr,
                    caption=caption,
                    parse_mode="Markdown"
                )

        except:

            await query.message.reply_text(
                caption,
                parse_mode="Markdown"
            )

    # APPROVE

    elif data.startswith("approve_"):

        _, user_id, pack = data.split("_")

        link = PACK_LINKS.get(pack)

        await context.bot.send_message(
            chat_id=int(user_id),
            text=(
                f"✅ PAYMENT APPROVED\n\n"
                f"📦 Pack: {pack.upper()}\n\n"
                f"🔗 ACCESS LINK:\n{link}"
            )
        )

        await query.edit_message_caption(
            caption="✅ Approved Successfully"
        )

    # REJECT

    elif data.startswith("reject_"):

        _, user_id = data.split("_")

        await context.bot.send_message(
            chat_id=int(user_id),
            text="❌ Payment Rejected\n\nSend Valid Screenshot."
        )

        await query.edit_message_caption(
            caption="❌ Rejected"
        )

    # ADMIN PANEL BUTTONS

    elif data == "online":

        await query.answer("✅ Bot Is Online")

    elif data == "payment":

        await query.answer("💳 Payments Active")

# =========================
# SCREENSHOT HANDLER
# =========================

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    pack = context.user_data.get("pack", "basic")

    username = user.username if user.username else "No Username"

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Approve",
                callback_data=f"approve_{user.id}_{pack}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"reject_{user.id}"
            )
        ]
    ]

    caption = (
        f"📩 NEW PAYMENT RECEIVED\n\n"
        f"👤 Name: {user.first_name}\n"
        f"🔗 Username: @{username}\n"
        f"🆔 Chat ID: {user.id}\n"
        f"📦 Pack: {pack.upper()}"
    )

    admin_msg = await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # AUTO DELETE AFTER 10 MINUTES

    context.job_queue.run_once(
        delete_message,
        600,
        data=(ADMIN_ID, admin_msg.message_id)
    )

    await update.message.reply_text(
        "✅ Screenshot Submitted\n⏳ Wait For Admin Approval"
    )

# =========================
# DELETE MESSAGE
# =========================

async def delete_message(context: ContextTypes.DEFAULT_TYPE):

    chat_id, msg_id = context.job.data

    try:
        await context.bot.delete_message(chat_id, msg_id)
    except:
        pass

# =========================
# ADMIN PANEL
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    text = (
        "👑 ADMIN PANEL\n\n"
        "🤖 Bot Status: ONLINE\n"
        "💳 Payment System: ACTIVE\n"
        "📚 Store: RUNNING\n\n"
        f"🆔 Admin ID: {ADMIN_ID}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📊 Bot Online",
                callback_data="online"
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Payments Active",
                callback_data="payment"
            )
        ]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    keep_alive()

    print("Bot Running...")

    bot = ApplicationBuilder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))

    bot.add_handler(CommandHandler("admin", admin))

    bot.add_handler(CallbackQueryHandler(buttons))

    bot.add_handler(
        MessageHandler(filters.PHOTO, photo)
    )

    bot.run_polling()
