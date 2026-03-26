import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import Forbidden

TOKEN = "YOUR_TOKEN_HERE"
OWNER_ID = 1413911915

DB_FILE = "users.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"users": [], "blocked": []}, f)

def load_db():
    with open(DB_FILE) as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

db = load_db()
users = set(db["users"])
blocked = set(db["blocked"])

user_data = {}

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 TXT → VCF", callback_data="txt"),
         InlineKeyboardButton("📁 VCF → TXT", callback_data="vcf")],

        [InlineKeyboardButton("🔗 MERGE VCF", callback_data="mergevcf"),
         InlineKeyboardButton("📝 MERGE TXT", callback_data="mergetxt")],

        [InlineKeyboardButton("🔢 NUM → VCF", callback_data="num")],

        [InlineKeyboardButton("♻️ RESET", callback_data="reset")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    if uid not in users:
        users.add(uid)
        db["users"] = list(users)
        save_db(db)

    user_data[uid] = {}

    await update.message.reply_text(
        "MZ CV BOT PRO 🚀\nDEVELOPER : @mzpanel\nBOT CHAT : @mzcvchat",
        reply_markup=menu()
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    msg = " ".join(context.args)
    ok, fail = 0, 0

    for u in users.copy():
        try:
            await context.bot.send_message(u, msg)
            ok += 1
        except:
            fail += 1

    await update.message.reply_text(f"Sent: {ok}\nFailed: {fail}")

async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text(f"Total Users: {len(users)}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = user_data.setdefault(uid, {})

    if q.data == "txt":
        data.update({"mode": "txt", "step": "wait_file"})
        await q.message.reply_text("Send TXT file")

    elif q.data == "vcf":
        data.update({"mode": "vcf", "files": []})
        await q.message.reply_text("Send VCF files\nThen use /done")

    elif q.data == "mergevcf":
        data.update({"mode": "mergevcf", "files": []})
        await q.message.reply_text("Send VCF files\nThen use /done")

    elif q.data == "mergetxt":
        data.update({"mode": "mergetxt", "files": []})
        await q.message.reply_text("Send TXT files\nThen use /done")

    elif q.data == "num":
        data.update({"mode": "num", "step": "count", "nums": []})
        await q.message.reply_text("How many numbers?")

    elif q.data == "reset":
        user_data[uid] = {}
        await q.message.reply_text("Reset Done ♻️")

async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = user_data.get(uid, {})

    doc = update.message.document
    file = await doc.get_file()
    name = doc.file_name

    await file.download_to_drive(name)

    if data.get("mode") == "txt" and data.get("step") == "wait_file":
        data["file"] = name
        data["step"] = "ask_split"
        await update.message.reply_text("How many contacts per file?")
    else:
        data.setdefault("files", []).append(name)

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = user_data.get(uid, {})

    if data.get("mode") == "vcf":
        for f in data["files"]:
            out = f.replace(".vcf", ".txt")
            with open(out, "w") as o:
                for l in open(f):
                    if "TEL" in l:
                        o.write(l.split(":")[1])
            await update.message.reply_document(open(out, "rb"))

    elif data.get("mode") == "mergevcf":
        with open("merged.vcf", "w") as o:
            for f in data["files"]:
                o.write(open(f).read())
        await update.message.reply_document(open("merged.vcf", "rb"))

    elif data.get("mode") == "mergetxt":
        with open("merged.txt", "w") as o:
            for f in data["files"]:
                o.write(open(f).read())
        await update.message.reply_document(open("merged.txt", "rb"))

    user_data[uid] = {}
    await update.message.reply_text("✅ Done")

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    t = update.message.text
    data = user_data.get(uid, {})

    if data.get("mode") == "txt":

        if data["step"] == "ask_split":
            data["split"] = int(t)
            data["step"] = "ask_filename"
            await update.message.reply_text("File name?")

        elif data["step"] == "ask_filename":
            data["fname"] = t
            data["step"] = "ask_contact"
            await update.message.reply_text("Contact name?")

        elif data["step"] == "ask_contact":
            nums = open(data["file"]).read().splitlines()

            split = data["split"]
            name = data["fname"]
            cname = t

            c = 1
            i = 1
            for x in range(0, len(nums), split):
                part = nums[x:x+split]
                fname = f"{name}_{i}.vcf"

                with open(fname, "w") as v:
                    for n in part:
                        v.write(f"BEGIN:VCARD\nVERSION:3.0\nFN:{cname} {c}\nTEL:{n}\nEND:VCARD\n")
                        c += 1

                await update.message.reply_document(open(fname, "rb"))
                i += 1

            user_data[uid] = {}
            await update.message.reply_text("✅ Done bro🔥")

    elif data.get("mode") == "num":

        if data["step"] == "count":
            data["total"] = int(t)
            data["step"] = "collect"
            await update.message.reply_text("Enter number 1 (+91...)")

        elif data["step"] == "collect":
            data["nums"].append(t)

            if len(data["nums"]) < data["total"]:
                await update.message.reply_text(f"Enter number {len(data['nums'])+1}")
            else:
                data["step"] = "name"
                await update.message.reply_text("Contacts name?")

        elif data["step"] == "name":
            data["name"] = t
            data["step"] = "file"
            await update.message.reply_text("File name?")

        elif data["step"] == "file":
            fname = f"{t}.vcf"

            with open(fname, "w") as v:
                for i, n in enumerate(data["nums"], 1):
                    v.write(f"BEGIN:VCARD\nVERSION:3.0\nFN:{data['name']} {i}\nTEL:{n}\nEND:VCARD\n")

            await update.message.reply_document(open(fname, "rb"))
            user_data[uid] = {}
            await update.message.reply_text("✅ Done bro🔥")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("users", users_cmd))
app.add_handler(CommandHandler("done", done))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.Document.ALL, file_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

print("🚀 Bot Running...")
app.run_polling()
