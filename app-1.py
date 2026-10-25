import io, re
from pathlib import Path
import streamlit as st
import telebot

st.set_page_config(page_title="GATE Converter Bot", page_icon="🤖")
TPL = (Path(__file__).parent / "template.html").read_text(encoding="utf8")


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


@st.cache_resource
def start_bot():
    bot = telebot.TeleBot(st.secrets["BOT_TOKEN"], threaded=True)

    @bot.message_handler(commands=["start"])
    def hello(m):
        bot.reply_to(m, "Quiz HTML file(s) bhejo (ek saath kitni bhi). Main GATE-style interface mein convert karke wapas bhej dunga.")

    @bot.message_handler(content_types=["document"])
    def doc(m):
        d = m.document
        fn = d.file_name or "quiz.html"
        if not fn.lower().endswith((".html", ".htm")):
            bot.reply_to(m, "Sirf .html file bhejo: " + fn)
            return
        try:
            data = bot.download_file(bot.get_file(d.file_id).file_path)
            out = convert(data.decode("utf8", "ignore"))
        except Exception as e:
            bot.reply_to(m, "Error: " + str(e))
            return
        if out is None:
            bot.reply_to(m, "Questions data nahi mila: " + fn)
            return
        f = io.BytesIO(out.encode("utf8"))
        f.name = re.sub(r"\.html?$", "", fn, flags=re.I) + "_GATE.html"
        bot.send_document(m.chat.id, f, caption=caption(m.caption, out))

    import threading
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    return bot


start_bot()
st.title("🤖 GATE Converter Bot")
st.success("Bot chal raha hai. Telegram par bot ko HTML files bhejo.")
