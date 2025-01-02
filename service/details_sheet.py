import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
import json
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()


class DetailsSheet:
    def __init__(self):
        self.SCOPE = [
            "https://www.googleapis.com/auth/spreadsheets"
        ]
        self.CREDS = Credentials.from_service_account_file(
            'creds.json', scopes=self.SCOPE)
        self.GSPREAD_CLIENT = gspread.authorize(self.CREDS)
        self.SHEET_ID = os.getenv('SHEET_ID')
        self.SHEET = self.GSPREAD_CLIENT.open_by_key(self.SHEET_ID)
        self.SERVICE = build('sheets', 'v4', credentials=self.CREDS)
        self.details_sheet = self.SHEET.worksheet("Details")

    def import_data(self, json_data):
        # Ensure json_data is a dictionary
        logger.info("Received data: %s", json_data)
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        date = json_data['date']
        amount = json_data['amount']
        currency = json_data['currency']
        trans_type = json_data['trans_type']
        category = json_data['category']
        note = json_data['note']
        account = json_data['account']
        values = [date, amount, currency, trans_type, category, note, account]
        return values

    def append_data_to_last_row(self, data):
        """
        Appends data to the last row of a Google Sheet.

        Args:
            sheet (gspread.Worksheet): The Google Sheet to append data to.
            data (list): A list of data to append to the last row.
        """
        # Call the Sheets API to append data
        response = self.details_sheet.append_row(values=data)
        return response


# details_sheet = SHEET.worksheet("Details")
# data_importer = DataImporter()
# values = data_importer.import_data(json_data)
# response = data_importer.append_data_to_last_row(details_sheet, values)
# print(response)
