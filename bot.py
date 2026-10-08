import telebot
from flask import Flask
import threading

# Apna Bot Token yahan dalein
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
bot = telebot.TeleBot(BOT_TOKEN)

# User ka data temporary save rakhne ke liye dabba
user_quiz_data = {}

# --- WEB SERVER (Render ke liye) ---
app = Flask(__name__)
@app.route('/')
def index():
    return "Quiz Creator Bot is Running 24/7!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)


# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "Hello! Main Quiz Creator Bot hu.\n\nEk-ek karke questions add karne ke liye /createquiz type karein.")


# --- STEP-BY-STEP QUIZ CREATION ---
@bot.message_handler(commands=['createquiz'])
def start_quiz(message):
    chat_id = message.chat.id
    # Ek naya khali set banana jisme questions save honge
    user_quiz_data[chat_id] = {"questions": []}
    
    msg = bot.reply_to(message, "Chaliye naya Quiz banate hain!\n\nSabse pehle apna **Pehla Question** type karein:")
    bot.register_next_step_handler(msg, process_question)

def process_question(message):
    # Agar user ne /done likha, toh quiz khatam kar do
    if message.text == '/done':
        finish_quiz(message)
        return
        
    chat_id = message.chat.id
    user_quiz_data[chat_id]['current_q'] = message.text
    
    msg = bot.reply_to(message, "Question save ho gaya! Ab iske **Options** bhejein, comma (,) lagakar.\n\nJaise: A, B, C, D")
    bot.register_next_step_handler(msg, process_options)

def process_options(message):
    chat_id = message.chat.id
    # Comma ke hisaab se options ko alag-alag karna
    options = [opt.strip() for opt in message.text.split(',')]
    
    # Telegram poll mein kam se kam 2 options hone chahiye
    if len(options) < 2 or len(options) > 10:
        msg = bot.reply_to(message, "Kam se kam 2 options hone chahiye. Kripya comma lagakar dobara options bhejein:")
        bot.register_next_step_handler(msg, process_options)
        return

    user_quiz_data[chat_id]['current_opts'] = options
    msg = bot.reply_to(message, "Sahi jawab ka number kaunsa hai? (Jaise agar dusra option sahi hai, toh 2 likhein):")
    bot.register_next_step_handler(msg, process_correct_option)

def process_correct_option(message):
    chat_id = message.chat.id
    try:
        # Ginti 0 se shuru hoti hai isliye -1 kiya
        correct_id = int(message.text.strip()) - 1
        
        # Check karna ki sahi number unhi options ke andar se ho
        if correct_id < 0 or correct_id >= len(user_quiz_data[chat_id]['current_opts']):
            raise ValueError
    except:
        msg = bot.reply_to(message, "Galat number! Kripya sahi option ka number dobara bhejein:")
        bot.register_next_step_handler(msg, process_correct_option)
        return

    # Ek poora question ban kar taiyar ho gaya, isko save kar lo
    q_dict = {
        "question": user_quiz_data[chat_id]['current_q'],
        "options": user_quiz_data[chat_id]['current_opts'],
        "correct_option_id": correct_id
    }
    user_quiz_data[chat_id]['questions'].append(q_dict)

    total_q = len(user_quiz_data[chat_id]['questions'])
    msg = bot.reply_to(message, f"✅ Question {total_q} add ho gaya!\n\nAgla naya question type karein, YA agar quiz ban gaya hai toh type karein: /done")
    
    # Wapas question wale step par bhej diya (Loop)
    bot.register_next_step_handler(msg, process_question)


def finish_quiz(message):
    chat_id = message.chat.id
    questions = user_quiz_data.get(chat_id, {}).get('questions', [])
    
    if not questions:
        bot.reply_to(message, "Aapne koi question add nahi kiya. Quiz cancel ho gaya.")
        return

    bot.reply_to(message, f"🎉 Aapka {len(questions)} questions ka Quiz tayyar hai! Yeh rahe aapke questions:")
    
    # Ek-ek karke saare save kiye hue questions bhej dena
    for q in questions:
        bot.send_poll(
            chat_id=chat_id,
            question=q["question"],
            options=q["options"],
            type='quiz',
            correct_option_id=q["correct_option_id"],
            is_anonymous=False
        )
    
    # Purana data saaf kar dena taaki agla quiz naya bane
    user_quiz_data.pop(chat_id, None)


# --- BOT KO CHALU RAKHNA ---
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    print("Step-by-Step Quiz Creator Bot is running...")
    bot.infinity_polling(none_stop=True)
