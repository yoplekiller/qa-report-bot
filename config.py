import os

CREDS_FILE = "qa-report-bot-495208-e89318293f59.json"
MASTER_SPREADSHEET_ID = "19JI_EgmR6J0AgMcWLfXO3gdUT4KII45bhJew0q_-UQ4"
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/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")
REPORT_TIME = "17:00"  # 매일 오후 5시 발송 (로컬 실행 시)
