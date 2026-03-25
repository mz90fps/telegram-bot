import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8718356402:AAGRDx337Ss64wlyrOZRDk9j5Mr-YVsdXcY"

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
    user_data[update.effective_user.id] = {}
    await update.message.reply_text(
        "MZ CV BOT PRO 🚀\nDEVELOPER : @mzpanel\nBOT CHAT : @mzcvchat",
        reply_markup=get_menu()
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

# 🔹 FILE HANDLER
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

    # TXT FLOW
    if mode == "txt":
        data["step"] = "ask_split"
        await update.message.reply_text("Enter contacts per file (eg: 50)")

    # VCF → TXT
    elif mode == "vcf":
        with open("output.txt", "w") as out:
            for f in files:
                with open(f) as file:
                    for line in file:
                        if "TEL" in line:
                            out.write(line.split(":")[1])
        await update.message.reply_document(open("output.txt", "rb"))
        await update.message.reply_text("✅ Done")

    # MERGE VCF
    elif mode == "mergevcf":
        with open("merged.vcf", "w") as out:
            for f in files:
                out.write(open(f).read())
        await update.message.reply_document(open("merged.vcf", "rb"))
        await update.message.reply_text("✅ Done")

    # MERGE TXT
    elif mode == "mergetxt":
        with open("merged.txt", "w") as out:
            for f in files:
                out.write(open(f).read())
        await update.message.reply_document(open("merged.txt", "rb"))
        await update.message.reply_text("✅ Done")

# 🔹 TEXT HANDLER
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    text = update.message.text
    data = user_data.get(user, {})

    # TXT → VCF FLOW
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

    # NUM → VCF
    elif data.get("mode") == "num":

        if data.get("step") == "ask_count":
            data["total"] = int(text)
            data["step"] = "collect"
            await update.message.reply_text("Enter number 1 (use country code eg: +91)")

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
            numbers = data["numbers"]
            name = data["name"]

            with open(f"{filename}.vcf", "w") as v:
                for i, num in enumerate(numbers, 1):
                    v.write(f"BEGIN:VCARD\nVERSION:3.0\nFN:{name} {i}\nTEL:{num}\nEND:VCARD\n")

            await update.message.reply_document(open(f"{filename}.vcf", "rb"))
            await update.message.reply_text("✅ Done")

# 🔹 RUN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("done", done))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

print("🚀 Bot Running...")
app.run_polling()