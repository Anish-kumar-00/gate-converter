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
    cap = (cap or "").replace("#", "")

    def g(p):
        m = re.search(p, cap, re.M | re.I)
        return m.group(0).strip() if m else None

    n = out.count('"sr_no"')
    t = re.search(r"<title>(.*?)</title>", out, re.S).group(1).strip()
    name = g(r"^.*test name:.*$")
    head = g(r"^.*✨.*✨.*$") or f"✨ {t} ✨"
    qs = g(r"^\s*QUESTIONS:.*$") or f"QUESTIONS: {n}"
    tm = g(r"^\s*TIME:.*$") or f"TIME: {180 if n == 65 else n * 3} MINUTES ⏱️"
    return (name + "\n\n" if name else "") + head + "\n" + qs + "\n" + tm


def fname(cap, out, fn):
    m = re.search(r"test name:\s*\(?(.*?)\)?\s*$", (cap or "").replace("#", ""), re.M | re.I)
    if m and m.group(1).strip():
        n = m.group(1)
    else:
        t = re.search(r"<title>(.*?)</title>", out, re.S).group(1)
        n = re.sub(r"^\s*\d+\.\)\s*|\s*-\s*Hindi\s*$", "", t.strip())
    n = re.sub(r'[\\/:*?"<>|]+', " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return (n or re.sub(r"\.html?$", "", fn, flags=re.I)) + ".html"


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
        f.name = fname(m.caption, out, fn)
        bot.send_document(m.chat.id, f, caption=caption(m.caption, out))

    import threading

    def run():
        import time
        while True:
            try:
                bot.infinity_polling(timeout=30, long_polling_timeout=30)
            except Exception:
                time.sleep(5)

    threading.Thread(target=run, daemon=True).start()
    return bot


start_bot()
st.title("🤖 GATE Converter Bot")
st.success("Bot chal raha hai. Telegram par bot ko HTML files bhejo.")