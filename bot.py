from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from keep_alive import keep_alive

# YAHAN APNA TOKEN AUR ID DALEIN (Jo aapne pehle dala tha)
BOT_TOKEN = "8815403425:AAFB57wfLZWVmbIQ1MPjjDHjp5lqsvQ1YXU"
ADMIN_ID = 7664016879

tracker = {}

# Naya Start Command Function
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hello! Main 24/7 Group Monitor Bot hoon. Mujhe apne group mein add karein aur Admin banayein taaki main members ko track kar saku.\n\nData dekhne ke liye /stats type karein.")

async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.new_chat_members:
        adder = update.message.from_user
        
        for new_member in update.message.new_chat_members:
            if new_member.id != adder.id:
                tracker[adder.id] = tracker.get(adder.id, 0) + 1
                context.bot_data[adder.id] = adder.first_name

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
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
    keep_alive() 
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start)) # Start command add kar diya gaya hai
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_members))
    
    print("Bot chalu ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
