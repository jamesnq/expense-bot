from openai import OpenAI
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class ChatGPT:
    prompt = """
    You are a helpful assistant that helps users to manage their finances in 2025. You will extract data from user notes by both English and Vietnamese.
    The user will input a transaction note in Vietnamese or English. You will extract data from the note and return the data in a JSON format, each field contains only one value.
    The JSON format should be:
    {
        "date": dd/mm/2025,
        "amount": number,
        "currency": "VND, USD",
        "trans_type": "Thu, Chi, Đổi",
        "category": "Ăn uống, Giải trí, Hóa đơn, Personal, Quà, Thu coin, Trả ví, Thu code, Trả code, Trả lương, Lương",
        "note": "note",
        "account": "VP, Momo, Paypal, Binance, Techcombank, VCB, Tsr"
    }

    With not related input, just return "Invalid input"
"""
    user_prompt = ""

    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.openai_api_key)

    def get_completion(self, model="gpt-4o-mini"):
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": self.user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,  # this is the degree of randomness of the model's output
        )
        logger.info(response.choices[0].message.content)
        return response.choices[0].message.content
