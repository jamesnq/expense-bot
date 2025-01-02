import logging
import os
from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
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
allowed_id = os.getenv('ALLOWED_ID')
telegram_bot_api_key = os.getenv('TELEGRAM_BOT_API_KEY')

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


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    chatgpt.user_prompt = update.message.text
    logger.info("Received message: %s", update.message.text)
    completion = chatgpt.get_completion()
    logger.info("Received response: %s", completion)
    if ("Invalid input" in completion):
        await update.message.reply_text(completion)
        return
    json_data = details_sheet.import_data(completion)
    logger.info("Received data: %s", json_data)
    response = details_sheet.append_data_to_last_row(json_data)
    logger.info("Received response: %s", response)
    await update.message.reply_text(response)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(telegram_bot_api_key).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
