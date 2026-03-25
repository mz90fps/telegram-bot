import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import Forbidden

# 🔥 KEEP ALIVE SERVER
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is alive"

def run():
    app_web.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 🔐 CONFIG
TOKEN = os.getenv("8718356402:AAEFfOf52TgJ1SLkiC-d2W_gtsUK48rYLE4")
OWNER_ID = 1413911915

user_data = {}
users = set()
blocked_users = set()

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

        if user_id != OWNER_ID:
            try:
                await context.bot.send_message(
                    OWNER_ID,
                    f"👤 New User Joined\n\nID: {user_id}\nName: {user.first_name}\nUsername: @{user.username}"
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
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Not allowed")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast your message")
        return

    msg = " ".join(context.args)

    success = 0
    failed = 0

    for u in users.copy():
        try:
            await context.bot.send_message(u, msg)
            success += 1
        except Forbidden:
            blocked_users.add(u)
            failed += 1
        except:
            failed += 1

    await update.message.reply_text(
        f"📢 Broadcast Done\n\n✅ Sent: {success}\n❌ Failed: {failed}"
    )

# 🔹 USERS
async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    total = len(users)
    blocked = len(blocked_users)
    active = total - blocked

    await update.message.reply_text(
        f"👥 USERS DATA\n\nTotal: {total}\nActive: {active}\nBlocked: {blocked}"
    )

# 🔹 BUTTON
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user.id
    data = user_data.setdefault(user, {})

    if query.data == "txttovcf":
        data.update({"mode": "txt", "files": [], "step": "wait"})
        await query.message.reply_text("📂 Send TXT file(s)\nThen type /done")

    elif query.data == "vcftotxt":
        data.update({"mode": "vcf", "files": []})
        await query.message.reply_text("📂 Send VCF files\nThen type /done")

    elif query.data == "mergevcf":
        data.update({"mode": "mergevcf", "files": []})
        await query.message.reply_text("📂 Send VCF files\nThen type /done")

    elif query.data == "mergetxt":
        data.update({"mode": "mergetxt", "files": []})
        await query.message.reply_text("📂 Send TXT files\nThen type /done")

    elif query.data == "numtovfc":
        data.update({"mode": "num", "step": "ask_count", "numbers": []})
        await query.message.reply_text("How many numbers? (eg: 3)")

    elif query.data == "reset":
        user_data[user] = {}
        await query.message.reply_text("♻️ Reset Done")

# 🔹 FILE
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    data = user_data.get(user, {})
    mode = data.get("mode")

    file = await update.message.document.get_file()
    name = update.message.document.file_name
    await file.download_to_drive(name)

    if mode in ["txt", "vcf", "mergevcf", "mergetxt"]:
        data.setdefault("files", []).append(name)

# 🔹 DONE
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    data = user_data.get(user, {})
    mode = data.get("mode")
    files = data.get("files", [])

    if mode == "txt":
        data["step"] = "ask_split"
        await update.message.reply_text("Enter contacts per file (eg: 50)")

    elif mode == "vcf":
        with open("output.txt", "w") as out:
            for f in files:
                with open(f) as file:
                    for line in file:
                        if "TEL" in line:
                            out.write(line.split(":")[1])
        await update.message.reply_document(open("output.txt", "rb"))

    elif mode == "mergevcf":
        with open("merged.vcf", "w") as out:
            for f in files:
                out.write(open(f).read())
        await update.message.reply_document(open("merged.vcf", "rb"))

    elif mode == "mergetxt":
        with open("merged.txt", "w") as out:
            for f in files:
                out.write(open(f).read())
        await update.message.reply_document(open("merged.txt", "rb"))

    await update.message.reply_text("✅ Done")

# 🔹 TEXT
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    text = update.message.text
    data = user_data.get(user, {})

    if data.get("mode") == "txt":

        if data.get("step") == "ask_split":
            data["split"] = int(text)
            data["step"] = "ask_filename"
            await update.message.reply_text("Enter file name")

        elif data.get("step") == "ask_filename":
            data["filename"] = text
            data["step"] = "ask_contact"
            await update.message.reply_text("Enter contact name")

        elif data.get("step") == "ask_contact":
            numbers = []
            for f in data.get("files", []):
                with open(f) as file:
                    numbers.extend(file.read().splitlines())

            split = data["split"]
            filename = data["filename"]
            contact = text

            count = 1
            file_index = 1

            for i in range(0, len(numbers), split):
                part = numbers[i:i+split]
                name = f"{filename}_{file_index}.vcf"

                with open(name, "w") as v:
                    for num in part:
                        v.write(f"BEGIN:VCARD\nVERSION:3.0\nFN:{contact} {count}\nTEL:{num}\nEND:VCARD\n")
                        count += 1

                await update.message.reply_document(open(name, "rb"))
                file_index += 1

            await update.message.reply_text("✅ Done")

# 🔹 RUN
keep_alive()  # 🔥 important

tg_app = ApplicationBuilder().token(TOKEN).build()

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("done", done))
tg_app.add_handler(CommandHandler("broadcast", broadcast))
tg_app.add_handler(CommandHandler("users", users_cmd))
tg_app.add_handler(CallbackQueryHandler(button_handler))
tg_app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

print("🚀 Bot Running...")
tg_app.run_polling()
