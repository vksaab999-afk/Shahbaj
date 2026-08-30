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
ADMIN_CHAT_ID = 5785924075

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

# --- KEEP-ALIVE WEB SERVER (FIXED FOR UPTIMEROBOT 501 ERROR) ---
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

# --- WELCOME MESSAGES SENDER FUNCTION ---
async def send_welcome_content(context: ContextTypes.DEFAULT_TYPE, user_id: int, first_name: str):
    try:
        welcome_text = (
            f"Welcome {first_name} ❤️‍🔥\n\n"
            f"Yrr aapne colour trading me aaj tak kitna bhi loss kia ho no problem sab recover ho jayega\n\n"
            f"100%\n\n"
            f"Niche ka video pura dekho or paisa chapo💸\n"
            f"⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️"
        )
        await context.bot.send_message(chat_id=user_id, text=welcome_text)

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

        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=SOURCE_CHAT_ID,
            message_id=AUDIO_MSG_ID
        )
    except Exception as e:
        logging.error(f"Could not send welcome content to user {user_id}: {e}")

# --- JOIN REQUEST HANDLER ---
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    user = request.from_user
    save_user_to_mongo(user.id, user.first_name, user.username)
    await send_welcome_content(context, user.id, user.first_name)

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user_to_mongo(user.id, user.first_name, user.username)
    await send_welcome_content(context, user.id, user.first_name)

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

# --- BULLET-PROOF BROADCAST LOGIC (FOR 50k+ USERS) ---
async def execute_broadcast(message_to_broadcast, context, admin_chat_id):
    users = list(users_collection.find({}, {"user_id": 1}))
    total_users = len(users)

    if total_users == 0:
        await context.bot.send_message(chat_id=admin_chat_id, text="⚠️ Database me koi user nahi hai!")
        return

    success = 0
    failed = 0

    progress_msg = await context.bot.send_message(
        chat_id=admin_chat_id, 
        text=f"🚀 **Broadcast Started!**\nTotal Users: `{total_users}`\nPlease wait..."
    )

    for index, u in enumerate(users):
        u_id = u["user_id"]
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
            
            success += 1
        except Exception as e:
            failed += 1
            logging.error(f"Error sending to {u_id}: {e}")

        # Telegram limit protect karne ke liye delay (Har 30 messages ke baad thoda extra rest taaki FloodWait na aaye)
        await asyncio.sleep(0.05)
        if index > 0 and index % 30 == 0:
            await asyncio.sleep(1.0)

    try:
        await context.bot.edit_message_text(
            chat_id=admin_chat_id, 
            message_id=progress_msg.message_id,
            text=f"✅ **Broadcast Completed!**\n\n👥 Total: `{total_users}`\n🚀 Sent: `{success}`\n❌ Failed: `{failed}`", 
            parse_mode="Markdown"
        )
    except:
        await context.bot.send_message(
            chat_id=admin_chat_id, 
            text=f"✅ **Broadcast Completed!**\n\n👥 Total: `{total_users}`\n🚀 Sent: `{success}`\n❌ Failed: `{failed}`", 
            parse_mode="Markdown"
        )

# --- 1. DIRECT AUTOMATIC BROADCAST ---
async def auto_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    if msg.text and msg.text.startswith("/"):
        return
    await execute_broadcast(msg, context, ADMIN_CHAT_ID)

# --- 2. COMMAND BASED BROADCAST ---
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    if msg.reply_to_message:
        await execute_broadcast(msg.reply_to_message, context, ADMIN_CHAT_ID)
    else:
        text_after_command = msg.text.replace("/broadcast", "").strip()
        if text_after_command:
            users = list(users_collection.find({}, {"user_id": 1}))
            total_users = len(users)
            success = 0
            failed = 0
            
            progress_msg = await msg.reply_text(f"🚀 Broadcast started for {total_users} users...")
            
            for index, u in enumerate(users):
                try:
                    await context.bot.send_message(chat_id=u["user_id"], text=text_after_command)
                    success += 1
                except:
                    failed += 1
                await asyncio.sleep(0.05)
                if index > 0 and index % 30 == 0:
                    await asyncio.sleep(1.0)
                    
            await progress_msg.edit_text(f"✅ **Broadcast Completed!**\n\n👥 Total: `{total_users}`\n🚀 Sent: `{success}`\n❌ Failed: `{failed}`", parse_mode="Markdown")
        else:
            await msg.reply_text("⚠️ Kripya message ke sath /broadcast likhein ya kisi message par reply karke /broadcast bhejein.")

# --- STATS COMMAND ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_CHAT_ID:
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
    
    # Direct Message Handler
    app.add_handler(MessageHandler(filters.Chat(ADMIN_CHAT_ID) & ~filters.COMMAND, auto_broadcast))

    print("Bot is running...")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
