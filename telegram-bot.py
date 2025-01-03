import logging
import os
import json
import threading
from dotenv import load_dotenv
from flask import Flask, request
from telegram import (
    ForceReply,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from ai.openai import ChatGPT
from service.details_sheet import DetailsSheet

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()
allowed_id = os.getenv("ALLOWED_ID")
telegram_bot_api_key = os.getenv("TELEGRAM_BOT_API_KEY")

chatgpt = ChatGPT()
details_sheet = DetailsSheet()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello", 200


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != allowed_id:
        update.message.reply_text("Unauthorized access.")
        return
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message:
        await update.message.reply_text(
            f"Replied to a message {update.message.chat.id}"
        )
        return
    user_message = update.message.text
    chatgpt.user_prompt = user_message
    message_type_json = chatgpt.classify_message()
    message_type = json.loads(message_type_json)
    logger.info(message_type)
    if message_type["type"] == "add":
        logger.info("=====add type=====")
        await handle_add_transaction(update, user_message, context)
    elif message_type["type"] == "edit":
        logger.info("=====edit type=====")
        await handle_edit_information(update, user_message, context)
    else:
        await update.message.reply_text("Invalid input")


async def handle_add_transaction(
    update: Update, user_message: str, context: ContextTypes.DEFAULT_TYPE
) -> None:
    extracted_data = chatgpt.get_extract_data()
    data = details_sheet.import_data(extracted_data)
    context.user_data["extracted_data"] = data
    logger.info(context.user_data["extracted_data"])
    await send_feedback_request(update.message.chat.id, data, context)


async def send_feedback_request(
    chat_id, data, context: ContextTypes.DEFAULT_TYPE
) -> None:
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data="approve"),
            InlineKeyboardButton("✏️ Edit", callback_data="edit"),
        ]
    ]
    response_message = f"Review again information: \n\n    Date: {data[0]}\n    Amount: {data[1]}\n    Currency: {data[2]}\n    Transaction type: {data[3]}\n    Category: {data[4]}\n    Note: {data[5]}\n    Account: {data[6]}"

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id, text=response_message, reply_markup=reply_markup
    )


async def handle_feedback(update, context):
    query = update.callback_query
    if query.data == "approve":
        response_json = details_sheet.append_data_to_last_row(
            context.user_data["extracted_data"]
        )
        response = json.loads(response_json)
        logger.info(response)
        await context.bot.answer_callback_query(
            callback_query_id=query.id, text=response["message"]
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id, text=response["message"]
        )
    elif query.data == "edit":
        await context.bot.answer_callback_query(
            callback_query_id=query.id, text="Coming soon."
        )


async def handle_edit_information(
    update: Update, user_message: str, context: ContextTypes.DEFAULT_TYPE
) -> None:
    extracted_data = chatgpt.get_extract_data()
    data = details_sheet.import_data(extracted_data)
    context.user_data["extracted_data"] = data
    logger.info(context.user_data["extracted_data"])
    await context.bot.edit_message_text(
        chat_id=update.message.chat_id,
        message_id=update.message.message_id,
        text="Review again information",
        reply_markup=None,
    )


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(telegram_bot_api_key).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, process_message)
    )
    application.add_handler(CallbackQueryHandler(handle_feedback))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def run_flask():
    """Run the Flask application."""
    app.run(host="0.0.0.0", port=3180)


if __name__ == "__main__":
    # Start the Flask app in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Start the Telegram bot
    main()
