import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram.error import Forbidden

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 1413911915

# 💾 DATABASE
DB_FILE = "users.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"users": [], "blocked": []}, f)

def load_db():
    return json.load(open(DB_FILE))

def save_db(data):
    json.dump(data, open(DB_FILE, "w"))

db = load_db()
users = set(db["users"])
blocked = set(db["blocked"])

user_data = {}

# 🔹 MENU
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 TXT → VCF", callback_data="txt")],
        [InlineKeyboardButton("📁 VCF → TXT", callback_data="vcf")],
        [InlineKeyboardButton("🔗 MERGE VCF", callback_data="mergevcf")],
        [InlineKeyboardButton("📝 MERGE TXT", callback_data="mergetxt")],
        [InlineKeyboardButton("🔢 NUM → VCF", callback_data="num")],
        [InlineKeyboardButton("♻️ RESET", callback_data="reset")]
    ])

# 🔹 START
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    uid = user.id

    if uid not in users:
        users.add(uid)
        db["users"] = list(users)
        save_db(db)

        if uid != OWNER_ID:
            try:
                context.bot.send_message(
                    OWNER_ID,
                    f"👤 New User\nID: {uid}\nName: {user.first_name}\n@{user.username}"
                )
            except:
                pass

    user_data[uid] = {}

    update.message.reply_text("MZ CV BOT PRO 🚀\nDEVELOPER : @mzpanel\nBOT CHAT : @mzcvchat", reply_markup=menu())

# 🔹 BROADCAST
def broadcast(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return

    msg = " ".join(context.args)
    ok, fail = 0, 0

    for u in users.copy():
        try:
            context.bot.send_message(u, msg)
            ok += 1
        except Forbidden:
            blocked.add(u)
            db["blocked"] = list(blocked)
            save_db(db)
            fail += 1
        except:
            fail += 1

    update.message.reply_text(f"Sent: {ok}\nFailed: {fail}")

# 🔹 USERS
def users_cmd(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return

    total = len(users)
    blocked_count = len(blocked)
    active = total - blocked_count

    update.message.reply_text(
        f"👥 Users\nTotal: {total}\nActive: {active}\nBlocked: {blocked_count}"
    )

# 🔹 BUTTON
def button(update: Update, context: CallbackContext):
    q = update.callback_query
    q.answer()

    uid = q.from_user.id
    data = user_data.setdefault(uid, {})

    if q.data == "txt":
        data.update({"mode": "txt", "step": "wait_file"})
        q.message.reply_text("Send TXT file")

    elif q.data == "vcf":
        data.update({"mode": "vcf", "files": []})
        q.message.reply_text("Send VCF files \nthen click /done")

    elif q.data == "mergevcf":
        data.update({"mode": "mergevcf", "files": []})
        q.message.reply_text("Send VCF files  \nthen click /done")

    elif q.data == "mergetxt":
        data.update({"mode": "mergetxt", "files": []})
        q.message.reply_text("Send TXT files  \nthen click /done")

    elif q.data == "num":
        data.update({"mode": "num", "step": "count", "nums": []})
        q.message.reply_text("How many numbers?(eg:3)")

    elif q.data == "reset":
        user_data[uid] = {}
        q.message.reply_text("Reset Done♻️")

# 🔹 FILE
def file_handler(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    data = user_data.get(uid, {})

    file = update.message.document.get_file()
    name = update.message.document.file_name
    file.download(name)

    if data.get("mode") == "txt" and data.get("step") == "wait_file":
        data["file"] = name
        data["step"] = "ask_split"
        update.message.reply_text("How much Contacts per file? (eg:50)")

    else:
        data.setdefault("files", []).append(name)

# 🔹 DONE
def done(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    data = user_data.get(uid, {})

    if data.get("mode") == "vcf":
        for f in data["files"]:
            out = f.replace(".vcf", ".txt")
            with open(out, "w") as o:
                for l in open(f):
                    if "TEL" in l:
                        o.write(l.split(":")[1])
            update.message.reply_document(open(out, "rb"))

    elif data.get("mode") == "mergevcf":
        with open("merged.vcf", "w") as o:
            for f in data["files"]:
                o.write(open(f).read())
        update.message.reply_document(open("merged.vcf", "rb"))

    elif data.get("mode") == "mergetxt":
        with open("merged.txt", "w") as o:
            for f in data["files"]:
                o.write(open(f).read())
        update.message.reply_document(open("merged.txt", "rb"))

    user_data[uid] = {}
    update.message.reply_text("✅ Done bro")

# 🔹 TEXT
def text(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    t = update.message.text
    data = user_data.get(uid, {})

    # TXT → VCF
    if data.get("mode") == "txt":

        if data["step"] == "ask_split":
            data["split"] = int(t)
            data["step"] = "ask_filename"
            update.message.reply_text("File name?")

        elif data["step"] == "ask_filename":
            data["fname"] = t
            data["step"] = "ask_contact"
            update.message.reply_text("Contacts name?")

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

                update.message.reply_document(open(fname, "rb"))
                i += 1

            user_data[uid] = {}
            update.message.reply_text("✅ Done bro")

    # NUM → VCF
    elif data.get("mode") == "num":

        if data["step"] == "count":
            data["total"] = int(t)
            data["step"] = "collect"
            update.message.reply_text("Enter number 1\n(include country code also (eg:+91****...)")

        elif data["step"] == "collect":
            data["nums"].append(t)

            if len(data["nums"]) < data["total"]:
                update.message.reply_text(f"Enter number {len(data['nums'])+1}")
            else:
                data["step"] = "name"
                update.message.reply_text("Contacts name?")

        elif data["step"] == "name":
            data["name"] = t
            data["step"] = "file"
            update.message.reply_text("File name?")

        elif data["step"] == "file":
            fname = f"{t}.vcf"

            with open(fname, "w") as v:
                for i, n in enumerate(data["nums"], 1):
                    v.write(f"BEGIN:VCARD\nVERSION:3.0\nFN:{data['name']} {i}\nTEL:{n}\nEND:VCARD\n")

            update.message.reply_document(open(fname, "rb"))
            user_data[uid] = {}
            update.message.reply_text("✅ Done bro")

# 🔹 RUN
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("broadcast", broadcast))
dp.add_handler(CommandHandler("users", users_cmd))
dp.add_handler(CommandHandler("done", done))
dp.add_handler(CallbackQueryHandler(button))
dp.add_handler(MessageHandler(Filters.document, file_handler))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text))

print("🚀 Bot Running...")
updater.start_polling()
updater.idle()
