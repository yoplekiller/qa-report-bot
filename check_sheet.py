import gspread
from google.oauth2.service_account import Credentials

# Define the scope and credentials for accessing the Google Sheets API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
CREDS_FILE = "qa-report-bot-495208-e89318293f59.json"
SPREADSHEET_ID = "13TEp02M5wEpYi8_woMuv7BU2kXpNJIu_voVn-rU7OdE"

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet(0)
data = sheet.get_all_values()

for row in data:
    print(row)