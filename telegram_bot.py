"""
Copyright (c) 2024. All rights reserved.

This code is licensed under a Custom License:
- You may use, copy, and modify this code for personal and non-commercial purposes.
- Commercial use, sale, or any financial exploitation of this code is strictly prohibited.
- All modifications must maintain this license header.
- No warranty is provided, and the author is not liable for any damages.
"""

import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters, ConversationHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))

# States for conversation
ADDING_USERNAME, REMOVING_USERNAME = range(2)

def send_menu(bot, chat_id):
    """Send menu message"""
    keyboard = [
        [InlineKeyboardButton("📋 List Usernames", callback_data='list')],
        [InlineKeyboardButton("➕ Add Username", callback_data='add')],
        [InlineKeyboardButton("❌ Remove Username", callback_data='remove')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        bot.send_message(
            chat_id=chat_id,
            text='Choose an action:',
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Error sending menu: {str(e)}")

def manage_command(update, context):
    """Handle commands from both channel and private chats"""
    try:
        # Print debug information
        print("Command received:")
        print(f"Update: {update}")
        
        # Handle channel posts differently
        if update.channel_post:
            chat_id = update.channel_post.chat_id
        else:
            chat_id = update.effective_chat.id
            
        send_menu(context.bot, chat_id)
    except Exception as e:
        print(f"Error in manage_command: {str(e)}")

def test_command(update, context):
    """Test command to verify bot's functionality"""
    try:
        chat_id = update.effective_chat.id
        context.bot.send_message(
            chat_id=chat_id,
            text="🔄 Test message - Bot is working!"
        )
        print(f"Test message sent to chat ID: {chat_id}")
    except Exception as e:
        print(f"Error in test_command: {str(e)}")

def load_usernames():
    """Load usernames from .env file"""
    return set(username.strip() for username in os.getenv("TARGET_USERNAMES", "").split(",") if username.strip())

def save_usernames(usernames):
    """Save usernames to .env file"""
    with open('.env', 'r') as file:
        lines = file.readlines()
    
    with open('.env', 'w') as file:
        for line in lines:
            if not line.startswith('TARGET_USERNAMES='):
                file.write(line)
        file.write(f'TARGET_USERNAMES={",".join(sorted(usernames))}\n')

def is_admin(update):
    """Check if the user is admin"""
    if update.effective_user:
        return update.effective_user.id == ADMIN_USER_ID
    elif update.callback_query:
        return update.callback_query.from_user.id == ADMIN_USER_ID
    return False

def button_callback(update, context):
    """Handle button presses"""
    query = update.callback_query
    query.answer()
    
    # Check if callback is from admin
    if not is_admin(update):
        query.edit_message_text("Sorry, you're not authorized to use this bot.")
        return ConversationHandler.END
    
    if query.data == 'list':
        usernames = load_usernames()
        if usernames:
            message = "📋 Current target usernames:\n\n" + "\n".join(f"• @{username}" for username in sorted(usernames))
        else:
            message = "No target usernames configured."
        query.edit_message_text(text=message, reply_markup=get_back_button())
        
    elif query.data == 'add':
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]]
        query.edit_message_text(
            text="To add a username, send it as a reply to this message (without @).\n\n"
                 "Or click Back to return to the menu.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADDING_USERNAME
        
    elif query.data == 'remove':
        usernames = load_usernames()
        if not usernames:
            query.edit_message_text(
                text="No usernames to remove.",
                reply_markup=get_back_button()
            )
            return ConversationHandler.END
            
        keyboard = [[InlineKeyboardButton(f"@{username}", callback_data=f"remove_{username}")] 
                   for username in sorted(usernames)]
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("Select username to remove:", reply_markup=reply_markup)
        return REMOVING_USERNAME

    elif query.data.startswith('remove_'):
        username = query.data.replace('remove_', '')
        usernames = load_usernames()
        if username in usernames:
            usernames.remove(username)
            save_usernames(usernames)
            query.edit_message_text(f"✅ Removed @{username} from target list.")
        else:
            query.edit_message_text(f"❌ Username @{username} not found in target list.")

def add_username(update, context):
    """Handle username addition"""
    if not is_admin(update):
        update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return ConversationHandler.END
        
    new_username = update.message.text.strip().replace('@', '')
    usernames = load_usernames()
    
    if new_username in usernames:
        update.message.reply_text(f"❌ @{new_username} is already in the target list.")
    else:
        usernames.add(new_username)
        save_usernames(usernames)
        update.message.reply_text(f"✅ Added @{new_username} to target list.")
    
    return ConversationHandler.END

def cancel(update, context):
    """Cancel the conversation"""
    update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END

def handle_username_message(update, context):
    """Handle username messages"""
    add_username(update, context)

def get_back_button():
    """Get back button"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]])

def handle_channel_command(update, context):
    """Handle any command from channel"""
    try:
        if update.channel_post and update.channel_post.text:
            command = update.channel_post.text.split()[0].lower()
            chat_id = update.channel_post.chat_id
            
            if command in ['/menu', '/manage', '/start']:
                send_menu(context.bot, chat_id)
            elif command == '/test':
                context.bot.send_message(
                    chat_id=chat_id,
                    text="🔄 Test message - Bot is working in channel!"
                )
    except Exception as e:
        print(f"Error handling channel command: {str(e)}")

def main():
    """Start the bot."""
    try:
        updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
        dp = updater.dispatcher

        # Add command handlers for both private messages and channel posts
        dp.add_handler(CommandHandler(['manage', 'start', 'menu'], manage_command))
        dp.add_handler(MessageHandler(
            Filters.command & Filters.chat_type.channel,
            manage_command
        ))
        
        # Add test command handler
        dp.add_handler(CommandHandler('test', test_command))
        dp.add_handler(MessageHandler(
            Filters.regex('^/test') & Filters.chat_type.channel,
            test_command
        ))

        # Add conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(button_callback)],
            states={
                ADDING_USERNAME: [
                    MessageHandler(Filters.text & ~Filters.command, handle_username_message),
                    CallbackQueryHandler(button_callback)
                ],
                REMOVING_USERNAME: [CallbackQueryHandler(button_callback)]
            },
            fallbacks=[CallbackQueryHandler(button_callback)]
        )
        dp.add_handler(conv_handler)

        # Add general channel command handler
        dp.add_handler(MessageHandler(
            Filters.chat_type.channel & Filters.command,
            handle_channel_command
        ))

        print("Bot started...")
        print(f"Channel ID: {TELEGRAM_CHANNEL_ID}")
        print(f"Admin ID: {ADMIN_USER_ID}")

        # Send initial test message to channel
        updater.bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text="🤖 Bot is online and ready!\n\nUse these commands:\n/menu - Show management menu\n/test - Test bot response"
        )

        updater.start_polling()
        updater.idle()

    except Exception as e:
        print(f"Error starting bot: {str(e)}")

if __name__ == '__main__':
    main() 