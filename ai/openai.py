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
    extract_info_prompt = """
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
    
    Example: 
    - User input: 2/1 103156 chi trả tiền render tech. Output: {"date": "02/01/2025", "amount": "103156", "currency": "VND", "trans_type": "Chi", "category": "Trả lương", "note": "trả tiền render", "account": "Techcombank"}
    - User input: 2/1 573k thu tiền coin nạp game zalo VP. Output: {"date": "02/01/2025", "amount": "573", "currency": "VND", "trans_type": "Thu", "category": "Thu coin", "note": "nạp game zalo", "account": "VP"}
    - Ammount "k" stand for thousand. Input: 231k Output: {"amount": "231000"}
    - Ammount in json always send with number type, not string.
    
    Return result in JSON format.
    {
        "date": dd/mm/2025,
        "amount": number,
        "currency": "VND, USD",
        "trans_type": "Thu, Chi, Đổi",
        "category": "Ăn uống, Giải trí, Hóa đơn, Personal, Quà, Thu coin, Trả ví, Thu code, Trả code, Trả lương, Lương",
        "note": "note",
        "account": "VP, Momo, Paypal, Binance, Techcombank, VCB, Tsr"
    }
    """

    classify_prompt = """
    You are a helpful assistant that helps user to classify their message into one of the following type:
    - Edit information
    - Add transaction
    
    Example for edit information:
    - Sửa ngày
    - Sửa số tiền
    - Sửa đơn vị tiền
    - Sửa kiểu giao dịch: Thu, Chi, Đổi
    - Sửa loại giao dịch: Ăn uống, Giải trí, Hóa đơn, Personal, Quà, Thu coin, Trả ví, Thu code, Trả code, Trả lương, Lương
    - Sửa ghi chú
    - Sửa tài khoản: VP, Momo, Paypal, Binance, Techcombank, VCB, Tsr

    Example for add transaction:
    - Ngày xxx 100k mua xxx VP
    - 2/1 573k thu tiền coin nạp game zalo VP
    
    Return result in JSON format:
    {
        "type": "edit" or "add",
    }
    
    With not related input, just return "invalid"
    """
    user_prompt = ""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key)

    def classify_message(self, model="gpt-4o-mini"):
        messages = [
            {"role": "system", "content": self.classify_prompt},
            {"role": "user", "content": self.user_prompt},
        ]
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,  # this is the degree of randomness of the model's output
            )
            message_type = response.choices[0].message.content
            return message_type
        except Exception as e:
            logger.error("Error processing message: %s", e)
            message_type = {}
            return message_type

    def get_extract_data(self, model="gpt-4o-mini"):
        messages = [
            {"role": "system", "content": self.extract_info_prompt},
            {"role": "user", "content": self.user_prompt},
        ]
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,  # this is the degree of randomness of the model's output
            )
            extracted_data = response.choices[0].message.content
            logger.info(extracted_data)
        except Exception as e:
            logger.error("Error processing message: %s", e)
            extracted_data = {}
        return extracted_data
