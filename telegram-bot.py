import logging
import os
from dotenv import load_dotenv
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
    chatgpt.user_prompt = update.message.text
    completion = chatgpt.get_completion()
    if "Invalid input" in completion:
        await update.message.reply_text(completion)
        return
    data = details_sheet.import_data(completion)
    # response = details_sheet.append_data_to_last_row(json_data)
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
        # response = details_sheet.append_data_to_last_row(json_data)
        logger.info("Approved data: %s", context.user_data["extracted_data"])
        context.bot.send_message(chat_id=query.message.chat_id, text="Data approved!")
    elif query.data == "edit":
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Please reply with corrections in JSON format.",
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

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
