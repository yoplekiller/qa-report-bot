import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
CREDS_FILE = "qa-report-bot-495208-e89318293f59.json"
MASTER_ID = "19JI_EgmR6J0AgMcWLfXO3gdUT4KII45bhJew0q_-UQ4"

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(MASTER_ID).get_worksheet(0)
data = sheet.get_all_values()

for i, row in enumerate(data):
    print(f"row {i}: {row}")
