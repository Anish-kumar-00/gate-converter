import io, os, re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN", "PASTE_YOUR_BOTFATHER_TOKEN_HERE")
TPL = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html"), encoding="utf8").read()

def convert(src):
    m = re.search(r"const questions = \[.*?\];\n", src, re.S)
    if not m:
        return None
    t = re.search(r"<title>(.*?)</title>", src, re.S)
    return TPL.replace("/*Q*/", m.group(0).rstrip()).replace("/*TITLE*/", t.group(1) if t else "GATE Test")

def caption(cap, out):
    if cap:
        return cap.replace("#", "")[:1024]
    t = re.search(r"<title>(.*?)</title>", out, re.S).group(1).strip()
    n = out.count('"sr_no"')
    return f"✨ {t} ✨\n\nOPEN IN YOUR BROWSER🌐  BEST IN CHROME\nQUESTIONS: {n}\nTIME: {180 if n == 65 else n * 3} MINUTES ⏱️"


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Quiz HTML file(s) bhejo (ek saath kitni bhi). Main GATE-style interface mein convert karke wapas bhej dunga.")

async def on_doc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = update.message.document
    if not d.file_name.lower().endswith((".html", ".htm")):
        await update.message.reply_text("Sirf .html file bhejo: " + d.file_name)
        return
    data = await (await d.get_file()).download_as_bytearray()
    out = convert(data.decode("utf8", "ignore"))
    if out is None:
        await update.message.reply_text("Questions data nahi mila: " + d.file_name)
        return
    name = re.sub(r"\.html?$", "", d.file_name, flags=re.I) + "_GATE.html"
    await update.message.reply_document(io.BytesIO(out.encode("utf8")), filename=name, caption=caption(update.message.caption, out))

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, on_doc))
app.run_polling()
