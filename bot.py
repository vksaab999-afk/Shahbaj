import os
import logging
import asyncio
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from threading import Thread
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ChatJoinRequestHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Logging Setup
logging.basicConfig(level=logging.INFO)

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8925919416:AAF3_9eOl3mGoTG2AEZbNnMQaAxO4UtMMX4" 

# Admin IDs list
ADMIN_IDS = [5785924075]

# MongoDB Atlas URI
MONGO_URI = "mongodb+srv://shahbaj:shahbaj0001@cluster0.06mgf1l.mongodb.net/?appName=Cluster0"

# Source Chat & Message IDs
SOURCE_CHAT_ID = 5785924075
WELCOME_MSG_ID = 26      # Text Welcome 
VIDEO_MSG_ID = 30        # Tutorial Video
AUDIO_MSG_ID = 34        # Audio Note
APK_MSG_ID = 32          # VIP Hack File

REGISTRATION_LINK = "https://bdg1.cc//#/register?invitationCode=qVhwk1416535"
# =======================================================

# --- MONGODB SETUP ---
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot_db"]
users_collection = db["users"]

def save_user_to_mongo(user_id, first_name, username):
    try:
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "first_name": first_name,
                    "username": username
                }
            },
            upsert=True
        )
    except Exception as e:
        logging.error(f"MongoDB Error: {e}")

# --- KEEP-ALIVE WEB SERVER ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is Live and MongoDB Connected!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = ThreadingHTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- INSTANT WELCOME SENDER FUNCTION ---
async def send_welcome_content(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        # 1. Send Welcome Text Message
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=SOURCE_CHAT_ID,
            message_id=WELCOME_MSG_ID
        )

        # 2. Send Video with Buttons
        keyboard = [
            [InlineKeyboardButton("Download Vip Hack 📥", callback_data="download_hack")],
            [InlineKeyboardButton("Registration Link 🔗", url=REGISTRATION_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=SOURCE_CHAT_ID,
            message_id=VIDEO_MSG_ID,
            reply_markup=reply_markup
        )

        # 3. Send Audio Note
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=SOURCE_CHAT_ID,
            message_id=AUDIO_MSG_ID
        )

        # 4. Special Gift Button with Deep-link
        bot_info = await context.bot.get_me()
        gift_link = f"https://t.me/{bot_info.username}?start=gift_claimed"
        
        gift_keyboard = [
            [InlineKeyboardButton("Claim Your Gift 🎁", url=gift_link)]
        ]
        gift_markup = InlineKeyboardMarkup(gift_keyboard)
        
        await context.bot.send_message(
            chat_id=user_id, 
            text="**Special Gift for you 🎊🤩**", 
            reply_markup=gift_markup, 
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Error sending welcome content to {user_id}: {e}")

# --- JOIN REQUEST HANDLER (INSTANT) ---
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    user = request.from_user
    save_user_to_mongo(user.id, user.first_name, user.username)
    # Background task for instant non-blocking execution
    asyncio.create_task(send_welcome_content(context, user.id))

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user_to_mongo(user.id, user.first_name, user.username)
    
    if context.args and "gift" in context.args[0]:
        await update.message.reply_text("Aap spacial gift ke liye Select ho chuke ho I'd bana ke uper diye username per screenshot bhej ke apna gift lelo 🎉🔥")
    else:
        asyncio.create_task(send_welcome_content(context, user.id))

# --- BUTTON HANDLER ---
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "download_hack":
        await context.bot.copy_message(
            chat_id=query.message.chat_id,
            from_chat_id=SOURCE_CHAT_ID,
            message_id=APK_MSG_ID
        )

# --- LIGHTNING FAST BROADCAST ENGINE ---
async def execute_broadcast(message_to_broadcast, context, admin_chat_id):
    users = list(users_collection.find({}, {"user_id": 1}))
    total_users = len(users)

    if total_users == 0:
        await context.bot.send_message(chat_id=admin_chat_id, text="⚠️ Database me koi user nahi hai!")
        return

    progress_msg = await context.bot.send_message(
        chat_id=admin_chat_id, 
        text=f"🚀 **Broadcast Started!**\nTotal Users: `{total_users}`\nPlease wait..."
    )

    for u in users:
        u_id = u["user_id"]
        if u_id in ADMIN_IDS:
            continue  # Admin ko khud message nahi jayega
        try:
            if message_to_broadcast.text:
                await context.bot.send_message(chat_id=u_id, text=message_to_broadcast.text, entities=message_to_broadcast.entities)
            elif message_to_broadcast.photo:
                await context.bot.send_photo(chat_id=u_id, photo=message_to_broadcast.photo[-1].file_id, caption=message_to_broadcast.caption, caption_entities=message_to_broadcast.caption_entities)
            elif message_to_broadcast.video:
                await context.bot.send_video(chat_id=u_id, video=message_to_broadcast.video.file_id, caption=message_to_broadcast.caption, caption_entities=message_to_broadcast.caption_entities)
            elif message_to_broadcast.audio:
                await context.bot.send_audio(chat_id=u_id, audio=message_to_broadcast.audio.file_id, caption=message_to_broadcast.caption, caption_entities=message_to_broadcast.caption_entities)
            elif message_to_broadcast.voice:
                await context.bot.send_voice(chat_id=u_id, voice=message_to_broadcast.voice.file_id, caption=message_to_broadcast.caption, caption_entities=message_to_broadcast.caption_entities)
            elif message_to_broadcast.document:
                await context.bot.send_document(chat_id=u_id, document=message_to_broadcast.document.file_id, caption=message_to_broadcast.caption, caption_entities=message_to_broadcast.caption_entities)
        except Exception as e:
            logging.error(f"Broadcast error for {u_id}: {e}")

    try:
        await context.bot.edit_message_text(
            chat_id=admin_chat_id, 
            message_id=progress_msg.message_id,
            text="✅ **Broadcast Completed!**", 
            parse_mode="Markdown"
        )
    except:
        await context.bot.send_message(
            chat_id=admin_chat_id, 
            text="✅ **Broadcast Completed!**", 
            parse_mode="Markdown"
        )

# --- AUTO BROADCAST FOR ADMINS ---
async def auto_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return
    if update.effective_user.id not in ADMIN_IDS:
        return
    if msg.text and msg.text.startswith("/"):
        return
    await execute_broadcast(msg, context, update.effective_user.id)

# --- COMMAND BASED BROADCAST ---
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    admin_id = update.effective_user.id
    if admin_id not in ADMIN_IDS:
        return

    if msg.reply_to_message:
        await execute_broadcast(msg.reply_to_message, context, admin_id)
    else:
        text_after_command = msg.text.replace("/broadcast", "").strip()
        if text_after_command:
            users = list(users_collection.find({}, {"user_id": 1}))
            total_users = len(users)
            
            progress_msg = await msg.reply_text(f"🚀 Broadcast started for {total_users} users...")
            
            for u in users:
                u_id = u["user_id"]
                if u_id in ADMIN_IDS:
                    continue
                try:
                    await context.bot.send_message(chat_id=u_id, text=text_after_command)
                except:
                    pass
                    
            await progress_msg.edit_text("✅ **Broadcast Completed!**", parse_mode="Markdown")
        else:
            await msg.reply_text("⚠️ Kripya message ke sath /broadcast likhein ya kisi message par reply karke /broadcast bhejein.")

# --- STATS COMMAND ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        total_users = users_collection.count_documents({})
        await update.message.reply_text(f"📊 **Total Users:** `{total_users}`", parse_mode="Markdown")

def main():
    Thread(target=run_web_server, daemon=True).start()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CallbackQueryHandler(handle_button))
    
    # Direct Message Handler for Admins
    app.add_handler(MessageHandler(filters.User(ADMIN_IDS) & ~filters.COMMAND, auto_broadcast))

    print("Bot is running...")
    app.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == "__main__":
    main()
