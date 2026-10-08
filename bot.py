import telebot
from flask import Flask
import threading

# Aapka exact Bot Token (Quotes '' ke andar)
BOT_TOKEN = '8366997355:AAEwVC00JMa5YolkLKUeKkE4S-LjpiN8AHs'
bot = telebot.TeleBot(BOT_TOKEN)

# Flask server jo bot ko 24/7 online rakhega
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is alive and running 24/7!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Start command
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "Hello! Main aapka Custom Quiz Bot hu. Naya question paane ke liye /quiz type karein.")

# Quiz command
@bot.message_handler(commands=['quiz'])
def send_quiz(message):
    question = "Python programming language kisne banayi thi?"
    options = ["Elon Musk", "Guido van Rossum", "Bill Gates", "Mark Zuckerberg"]
    
    bot.send_poll(
        chat_id=message.chat.id,
        question=question,
        options=options,
        type='quiz',
        correct_option_id=1,  # 1 matlab dusra option (Guido van Rossum)
        is_anonymous=False,
        explanation="Guido van Rossum ne 1991 mein Python banayi thi."
    )

# Ek sath Server aur Bot ko run karna
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    
    print("Bot is running...")
    # Polling start karna (none_stop=True ensures ki choti errors se bot band na ho)
    bot.infinity_polling(none_stop=True)
