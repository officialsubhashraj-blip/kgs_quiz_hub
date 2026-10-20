from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from keep_alive import keep_alive

# Aapki details yahan add kar di gayi hain
BOT_TOKEN = "8916607366:AAF2vSYcEOAgJg0phP9VdkB3tclmkvuaM5U"
ADMIN_ID = 7664016879

tracker = {}

async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.new_chat_members:
        adder = update.message.from_user
        
        for new_member in update.message.new_chat_members:
            if new_member.id != adder.id:
                tracker[adder.id] = tracker.get(adder.id, 0) + 1
                context.bot_data[adder.id] = adder.first_name

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Check karega ki command aapne hi di hai
    if user_id == ADMIN_ID:
        if not tracker:
            await update.message.reply_text("Abhi tak kisi ne koi naya member add nahi kiya hai.")
            return
        
        msg = "📊 **Group Invitation Stats:**\n\n"
        for uid, count in tracker.items():
            name = context.bot_data.get(uid, f"User_{uid}")
            msg += f"👤 {name}: {count} members add kiye\n"
            
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("🚫 Aapko ye command use karne ki permission nahi hai.")

def main():
    keep_alive() # Yeh server start karega
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_members))
    app.add_handler(CommandHandler("stats", show_stats))
    
    print("Bot chalu ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
