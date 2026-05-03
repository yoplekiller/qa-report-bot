import gspread
from google.oauth2.service_account import Credentials

# Define the scope and credentials for accessing the Google Sheets API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
CREDS_FILE = "qa-report-bot-495208-e89318293f59.json"
SPREADSHEET_ID = "13TEp02M5wEpYi8_woMuv7BU2kXpNJIu_voVn-rU7OdE"

# Authenticate and access the Google Sheet
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet(0)
data = sheet.get_all_values()

print("=== 섹션1 키 hex ===")
for row in data[2:5]:
    key = row[0]
    print(key.encode('utf-8').hex(), '|', key.encode('unicode_escape'))

print("\n=== 섹션2 키 hex ===")
for row in data[13:16]:
    key = row[0]
    print(key.encode('utf-8').hex(), '|', key.encode('unicode_escape'))

# 코드에서 사용 중인 키와 비교
test_key = "트래블링_TC"
print(f"\n코드 키 hex: {test_key.encode('utf-8').hex()}")
print(f"일치 여부: {data[2][0] == test_key}")
