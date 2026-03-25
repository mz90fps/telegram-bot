import os
import json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import Forbidden

# 🔥 KEEP ALIVE
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is alive"

def run():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 🔐 CONFIG
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 1413911915

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN not found")

# 💾 DATABASE
DB_FILE = "users.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": [], "blocked": []}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

db = load_db()
users = set(db["users"])
blocked_users = set(db["blocked"])

user_data = {}

# 🔹 MENU
def get_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 TXT → VCF", callback_data="txttovcf"),
         InlineKeyboardButton("📁 VCF → TXT", callback_data="vcftotxt")],
        [InlineKeyboardButton("🔗 MERGE VCF", callback_data="mergevcf"),
         InlineKeyboardButton("📝 MERGE TXT", callback_data="mergetxt")],
        [InlineKeyboardButton("🔢 NUM → VCF", callback_data="numtovfc")],
        [InlineKeyboardButton("♻️ RESET", callback_data="reset")]
    ])

# 🔹 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id not in users:
        users.add(user_id)
        db["users"] = list(users)
        save_db(db)

        if user_id != OWNER_ID:
            try:
                await context.bot.send_message(
                    OWNER_ID,
                    f"👤 New User Joined\nID: {user_id}\nName: {user.first_name}\nUsername: @{user.username}"
                )
            except:
                pass

    user_data[user_id] = {}

    await update.message.reply_text(
        "MZ CV BOT PRO 🚀\nDEVELOPER : @mzpanel\nBOT CHAT : @mzcvchat",
        reply_markup=get_menu()
    )

# 🔹 BROADCAST
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    msg = " ".join(context.args)

    success, failed = 0, 0

    for u in users.copy():
        try:
            await context.bot.send_message(u, msg)
            success += 1
        except Forbidden:
            blocked_users.add(u)
            db["blocked"] = list(blocked_users)
            save_db(db)
            failed += 1
        except:
            failed += 1

    await update.message.reply_text(f"✅ Sent: {success}\n❌ Failed: {failed}")

# 🔹 USERS
async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    total = len(users)
    blocked = len(blocked_users)
    active = total - blocked

    await update.message.reply_text(
        f"👥 USERS DATA\nTotal: {total}\nActive: {active}\nBlocked: {blocked}"
    )

# 🔹 BUTTON
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user.id
    data = user_data.setdefault(user, {})

    if query.data == "numtovfc":
        data["mode"] = "num"
        data["numbers"] = []
        data["step"] = "ask_count"
        await query.message.reply_text("How many numbers?")

# 🔹 TEXT HANDLER
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    text = update.message.text
    data = user_data.get(user, {})

    # 🔢 NUM → VCF FIXED
    if data.get("mode") == "num":

        if data.get("step") == "ask_count":
            data["total"] = int(text)
            data["step"] = "collect"
            await update.message.reply_text("Enter number 1")

        elif data.get("step") == "collect":
            data["numbers"].append(text)

            if len(data["numbers"]) < data["total"]:
                await update.message.reply_text(f"Enter number {len(data['numbers'])+1}")
            else:
                data["step"] = "ask_name"
                await update.message.reply_text("Enter contact name")

        elif data.get("step") == "ask_name":
            data["name"] = text
            data["step"] = "ask_file"
            await update.message.reply_text("Enter file name")

        elif data.get("step") == "ask_file":
            filename = text
            name = data["name"]

            with open(f"{filename}.vcf", "w") as v:
                for i, num in enumerate(data["numbers"], 1):
                    v.write(f"BEGIN:VCARD\nVERSION:3.0\nFN:{name} {i}\nTEL:{num}\nEND:VCARD\n")

            await update.message.reply_document(open(f"{filename}.vcf", "rb"))
            await update.message.reply_text("✅ Done")

# 🔹 RUN
keep_alive()

tg_app = ApplicationBuilder().token(TOKEN).build()

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("broadcast", broadcast))
tg_app.add_handler(CommandHandler("users", users_cmd))
tg_app.add_handler(CallbackQueryHandler(button_handler))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

print("🚀 Bot Running...")
tg_app.run_polling()
