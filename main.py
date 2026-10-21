
import os
import sqlite3
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    ChatMemberHandler,
    ContextTypes,
)

TOKEN = os.environ["8299633752:AAGaanGnfMtr16fX0H6Za0ieL_Xua3NCTGA"]
GROUP_ID = int(os.environ["1003994741642"])
DB_PATH = os.environ.get("DB_PATH", "invites.db")
REQUIRED = 2

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("group_guard")


def db():
    return sqlite3.connect(DB_PATH)


def init_db():
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS links (
                link TEXT PRIMARY KEY,
                inviter INTEGER NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS invites (
                inviter INTEGER NOT NULL,
                invitee INTEGER NOT NULL UNIQUE
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS restricted (
                user_id INTEGER PRIMARY KEY
            )
        """)


def invite_count(user_id):
    with db() as con:
        return con.execute(
            "SELECT COUNT(*) FROM invites WHERE inviter=?",
            (user_id,),
        ).fetchone()[0]


def is_restricted(user_id):
    with db() as con:
        return con.execute(
            "SELECT 1 FROM restricted WHERE user_id=?",
            (user_id,),
        ).fetchone() is not None


async def create_personal_link(context, user_id):
    link = await context.bot.create_chat_invite_link(
        chat_id=GROUP_ID,
        name=f"member-{user_id}",
    )
    with db() as con:
        con.execute(
            "INSERT OR REPLACE INTO links(link, inviter) VALUES(?, ?)",
            (link.invite_link, user_id),
        )
    return link.invite_link


async def unrestrict(context, user_id):
    if not is_restricted(user_id):
        return
    if invite_count(user_id) < REQUIRED:
        return

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
            can_add_web_page_previews=True,
        ),
    )

    with db() as con:
        con.execute(
            "DELETE FROM restricted WHERE user_id=?",
            (user_id,),
        )

    await context.bot.send_message(
        GROUP_ID,
        f"✅ Member {user_id} ke 2 invites poore ho gaye. "
        "Ab woh message bhej sakte hain.",
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Namaste! Group mein message bhejne ke liye "
        "2 naye members invite karne honge."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    count = invite_count(user.id)

    if is_restricted(user.id):
        message = (
            f"📊 Aapke invites: {count}/{REQUIRED}\n"
            "Restriction abhi lagi hui hai."
        )
    else:
        message = (
            f"📊 Aapke invites: {count}/{REQUIRED}\n"
            "Aap restricted nahi hain."
        )

    await update.effective_message.reply_text(message)


async def handle_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    event = update.chat_member
    if not event or event.chat.id != GROUP_ID:
        return

    old = event.old_chat_member
    new = event.new_chat_member
    user = new.user

    was_in = old.status in ("member", "administrator", "creator")
    is_in = new.status in ("member", "administrator", "creator")

    if was_in == is_in:
        return

    if was_in and not is_in:
        # Remove credit if an invited member leaves.
        with db() as con:
            con.execute(
                "DELETE FROM invites WHERE invitee=?",
                (user.id,),
            )
            con.execute(
                "DELETE FROM restricted WHERE user_id=?",
                (user.id,),
            )
        return

    if not is_in or user.is_bot:
        return

    admins = await context.bot.get_chat_administrators(GROUP_ID)
    if any(a.user.id == user.id for a in admins):
        return

    # Restrict the new member first.
    try:
        await context.bot.restrict_chat_member(
            chat_id=GROUP_ID,
            user_id=user.id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            ),
        )
    except Exception:
        log.exception("Could not restrict new member")
        return

    with db() as con:
        con.execute(
            "INSERT OR IGNORE INTO restricted(user_id) VALUES(?)",
            (user.id,),
        )

    # Credit only joins through this bot's recorded links.
    inviter = None
    if event.invite_link:
        with db() as con:
            row = con.execute(
                "SELECT inviter FROM links WHERE link=?",
                (event.invite_link.invite_link,),
            ).fetchone()
        if row:
            inviter = row[0]

    if inviter and inviter != user.id:
        with db() as con:
            con.execute(
                "INSERT OR IGNORE INTO invites(inviter, invitee) "
                "VALUES(?, ?)",
                (inviter, user.id),
            )
        await unrestrict(context, inviter)

    # Give the new member their own invite link.
    try:
        link = await create_personal_link(context, user.id)
        await context.bot.send_message(
            GROUP_ID,
            f"👋 Welcome, {user.full_name}!\n"
            f"Message bhejne ke liye {REQUIRED} naye members invite karein.\n"
            f"Progress: {invite_count(user.id)}/{REQUIRED}\n"
            f"Aapka personal invite link:\n{link}",
        )
    except Exception:
        log.exception("Could not create/send invite link")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, *args):
        pass


def main():
    init_db()

    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    Thread(target=server.serve_forever, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mystatus", status))
    app.add_handler(
        ChatMemberHandler(
            handle_member,
            ChatMemberHandler.CHAT_MEMBER,
        )
    )
    app.run_polling(allowed_updates=["message", "chat_member"])


if __name__ == "__main__":
    main()
