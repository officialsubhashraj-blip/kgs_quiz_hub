from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from keep_alive import keep_alive

# Yahan apna Token aur ID dalein
BOT_TOKEN = "8846698403:AAHtYNMiEsTwzTQssVDO5x4RL0tOxqX4kbE"
ADMIN_ID = 7664016879

# Kitne members add karne par chat khulegi
REQUIRED_ADDS = 3

tracker = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hello! Main ek Strict Group Monitor Bot hoon. Naye members ko chat karne ke liye 3 dosto ko add karna hoga.\n\nData dekhne ke liye /stats type karein.")

async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    if update.message.new_chat_members:
        adder = update.message.from_user # Jisne add kiya hai
        
        for new_member in update.message.new_chat_members:
            # Agar bot add hua hai toh usko ignore karein
            if new_member.is_bot:
                continue
                
            # Agar kisi ne direct kisi aur ko add kiya hai
            if new_member.id != adder.id:
                # Adder ka score badhayein
                tracker[adder.id] = tracker.get(adder.id, 0) + 1
                context.bot_data[adder.id] = adder.first_name
                
                total_added = tracker[adder.id]
                
                # Check karein ki kya usne 3 members pure kar liye
                if total_added >= REQUIRED_ADDS:
                    try:
                        # User ko Unmute (Chat allow) karein
                        await context.bot.restrict_chat_member(
                            chat_id=chat_id,
                            user_id=adder.id,
                            permissions=ChatPermissions(
                                can_send_messages=True,
                                can_send_media_messages=True,
                                can_send_other_messages=True,
                                can_add_web_page_previews=True
                            )
                        )
                        await update.message.reply_text(f"🎉 **{adder.first_name}** ne {REQUIRED_ADDS} members add kar diye hain!\n🔓 Ab inka chat unlock ho gaya hai.", parse_mode='Markdown')
                    except Exception:
                        pass # Agar user already admin hai toh error ignore karega
                else:
                    bach gaye = REQUIRED_ADDS - total_added
                    await update.message.reply_text(f"👍 **{adder.first_name}** ne **{new_member.first_name}** ko add kiya.\n🔒 Chat unlock karne ke liye abhi {bach gaye} aur members add karne honge.", parse_mode='Markdown')

            # Naya aane wala member (chahe link se aaye ya koi add kare), usko Mute karein
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=new_member.id,
                    permissions=ChatPermissions(can_send_messages=False)
                )
                await update.message.reply_text(f"🛑 Welcome **{new_member.first_name}**!\n\nAap abhi group mein message nahi bhej sakte. Chat unlock karne ke liye aapko group mein **{REQUIRED_ADDS} naye members** ko add karna hoga.", parse_mode='Markdown')
            except Exception:
                pass # Agar join hone wala admin hai, toh use mute nahi karega

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id == ADMIN_ID:
        if not tracker:
            await update.message.reply_text("Abhi tak kisi ne koi naya member add nahi kiya hai.")
            return
        
        msg = "📊 **Group Invitation Stats:**\n\n"
        for uid, count in tracker.items():
            name = context.bot_data.get(uid, f"User_{uid}")
            status = "🔓 Unlocked" if count >= REQUIRED_ADDS else "🔒 Locked"
            msg += f"👤 {name}: {count} members ({status})\n"
            
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("🚫 Aapko ye command use karne ki permission nahi hai.")

def main():
    keep_alive() 
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_members))
    
    print("Bot chalu ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
