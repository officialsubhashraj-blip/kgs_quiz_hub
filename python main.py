
import os
import sqlite3
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

from telegram import Update, ChatPermissions
from telegram.ext import (
    Application, CommandHandler, ChatMemberHandler,
    ContextTypes
)

TOKEN = os.environ["8299633752:AAGaanGnfMtr16fX0H6Za0ieL_Xua3NCTGA"]
GROUP_ID = int(os.environ["1003994741642"])
REQUIRED_INVITES = 2
DB = os.environ.get("DB_PATH", "invites.db")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS links (
                link TEXT PRIMARY KEY,
                inviter INTEGER NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS invited (
                inviter INTEGER NOT NULL,
                invitee INTEGER NOT NULL,
                PRIMARY KEY(inviter, invitee)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS restricted (
                user_id INTEGER PRIMARY KEY
            )
        """)


def count_invites(user_id):
    with sqlite3.connect(DB) as con:
        return con.execute(
            "SELECT COUNT(*) FROM invited WHERE inviter=?",
            (user_id,)
        ).fetchone()[0]


def is_restricted(user_id):
    with sqlite3.connect(DB) as con:
        return con.execute(
            "SELECT 1 FROM restricted WHERE user_id=?",
            (user_id,)
        ).fetchone() is not None


def save_link(link, inviter):
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT OR REPLACE INTO links(link, inviter) VALUES(?, ?)",
            (link, inviter)
        )


async def make_invite(context, user_id):
    link = await context.bot.create_chat_invite_link(
        chat_id=GROUP_ID,
        name=f"invite-{user_id}"
    )
    save_link(link.invite_link, user_id)
    return link.invite_link


async def release_if_eligible(context, user_id):
    if (is_restricted(user_id)
            and count_invites(user_id) >= REQUIRED_INVITES):
        await context.bot.restrict_chat_member(
            chat_id=GROUP_ID,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        with sqlite3.connect(DB) as con:
            con.execute(
                "DELETE FROM restricted WHERE user_id=?",
                (user_id,)
            )
        await context.bot.send_message(
            GROUP_ID,
            f"✅ User {user_id} ne 2 members invite kar liye. "
            "Ab messaging restriction hata di gayi hai."
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Yeh group protection bot hai. "
        "Naye members ke liye invite verification group mein hota hai."
    )


async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    event = update.chat_member
    if not event or event.chat.id != GROUP_ID:
        return

    old = event.old_chat_member
    new = event.new_chat_member
    user = new.user

    was_member = old.status in ("member", "administrator", "creator")
    now_member = new.status in ("member", "administrator", "creator")

    if was_member == now_member:
        return

    # A member left or was removed: remove their direct invite credit.
    if was_member and not now_member:
        with sqlite3.connect(DB) as con:
            con.execute("DELETE FROM invited WHERE invitee=?", (user.id,))
            con.execute("DELETE FROM restricted WHERE user_id=?", (user.id,))
        return

    if not now_member or user.is_bot:
        return

    # Do not restrict group admins or the owner.
    try:
        admins = await context.bot.get_chat_administrators(GROUP_ID)
        if any(admin.user.id == user.id for admin in admins):
            return
    except Exception:
        log.exception("Could not check group admins")
        return

    invite = event.invite_link
    inviter_id = None

    if invite:
        with sqlite3.connect(DB) as con:
            row = con.execute(
                "SELECT inviter FROM links WHERE link=?",
                (invite.invite_link,)
            ).fetchone()
            if row:
                inviter_id = row[0]

    # Restrict every new non-admin until their own invite target is met.
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT OR IGNORE INTO restricted(user_id) VALUES(?)",
            (user.id,)
        )

    try:
        await context.bot.restrict_chat_member(
            chat_id=GROUP_ID,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
    except Exception:
        log.exception("Could not restrict new member %s", user.id)
        return

    # Count only first-time, distinct invitees from links made by this bot.
    if inviter_id and inviter_id != user.id:
        with sqlite3.connect(DB) as con:
            con.execute(
                "INSERT OR IGNORE INTO invited(inviter, invitee) "
                "VALUES(?, ?)",
                (inviter_id, user.id)
            )
        await release_if_eligible(context, inviter_id)

    try:
        personal_link = await make_invite(context, user.id)
        progress = count_invites(user.id)
        await context.bot.send_message(
            GROUP_ID,
            f"👋 Welcome, {user.full_name}!\n"
            f"Message bhejne ke liye 2 members invite karein.\n"
            f"Aapke invites: {progress}/{REQUIRED_INVITES}\n"
            f"Aapka personal invite link:\n{personal_link}"
        )
    except Exception:
        log.exception("Could not create or send personal invite link")


async def my_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    count = count_invites(user_id)
    await update.effective_message.reply_text(
        f"Aapke verified invites: {count}/{REQUIRED_INVITES}\n"
        + ("Aap message bhej sakte hain."
           if not is_restricted(user_id)
           else "Aap abhi restricted hain.")
    )


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot service running")

    def log_message(self, *args):
        pass


def run_health_server():
    port = int(os.environ.get("PORT", "8080"))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


def main():
    init_db()

    # HTTP endpoint for hosting platforms that require a web service.
    Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mystatus", my_status))
    app.add_handler(
        ChatMemberHandler(new_member, ChatMemberHandler.CHAT_MEMBER)
    )

    app.run_polling(
        allowed_updates=["message", "chat_member"]
    )


if __name__ == "__main__":
    main()
