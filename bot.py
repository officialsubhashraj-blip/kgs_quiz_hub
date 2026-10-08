import telebot
from flask import Flask
import threading

# Yahan BotFather wala token dalein
BOT_TOKEN = '8366997355:AAEwVC00JMa5YolkLKUeKkE4S-LjpiN8AHs' 
bot = telebot.TeleBot(BOT_TOKEN)

# Yeh Flask server cloud hosting ko batayega ki app chal rahi hai
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot 24/7 running hai!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Bot ka basic Start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello! Main online aa gaya hu.")

# Server aur bot ko ek sath chalana
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
