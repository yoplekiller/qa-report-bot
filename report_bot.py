import sys
import re
import gspread
import requests
import schedule
import time
from datetime import datetime, date, timezone, timedelta
from google.oauth2.service_account import Credentials

KST = timezone(timedelta(hours=9))
from config import CREDS_FILE, MASTER_SPREADSHEET_ID, SLACK_WEBHOOK_URL, REPORT_TIME

sys.stdout.reconfigure(encoding='utf-8')

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_gspread_client():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def extract_spreadsheet_id(url):
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None

# 구글 시트에서 활성 프로젝트 목록 가져오기
def get_active_projects(client):
    sheet = client.open_by_key(MASTER_SPREADSHEET_ID).get_worksheet(0)
    rows = sheet.get_all_values()[1:]  # 헤더 제외
    today = datetime.now(KST).date()
    active = []

    for row in rows:
        if len(row) < 4:
            continue
        project_name, sheet_url, start_str, end_str = row[0], row[1], row[2], row[3]

        # 시작일/종료일 둘 다 있어야 활성화
        if not start_str or not end_str:
            continue

        try:
            start = datetime.strptime(start_str, "%Y-%m-%d").date()
            end = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"⚠️ 날짜 형식 오류 [{project_name}]: {start_str} ~ {end_str}")
            continue

        if start <= today <= end:
            spreadsheet_id = extract_spreadsheet_id(sheet_url)
            if spreadsheet_id:
                active.append({"name": project_name, "id": spreadsheet_id, "start": start_str, "end": end_str})

    return active


def get_sheet_data(client, spreadsheet_id):
    sheet = client.open_by_key(spreadsheet_id).get_worksheet(0)
    return sheet.get_all_values()


def parse_test_status(data):
    rows = {}
    for row in data[2:5]:
        if row[0]:
            rows[row[0]] = row
    return rows


def parse_automation_coverage(data):
    rows = {}
    for row in data[13:16]:
        if row[0]:
            rows[row[0]] = row
    return rows


def calc_rate(numerator, denominator):
    try:
        n, d = int(numerator), int(denominator)
        if d == 0:
            return "0%"
        return f"{round(n / d * 100)}%"
    except (ValueError, TypeError):
        return "-"


def build_slack_message(project_name, data, start_date="", end_date="", spreadsheet_id=""):
    now_kst = datetime.now(KST)
    today = now_kst.strftime("%Y-%m-%d %H:%M KST")
    status_rows = parse_test_status(data)

    total_status = status_rows.get("전체", ["-"] * 10)
    api_status = status_rows.get("API_TC", ["-"] * 10)
    area_keys = [k for k in status_rows if k not in ("전체", "API_TC")]

    area_fields = []
    for key in area_keys:
        s = status_rows[key]
        label = key.replace("_TC", "")
        rate = calc_rate(s[2], s[1])
        area_fields.append({"type": "mrkdwn", "text": f"*{label}*\nPASS {s[3]} / FAIL {s[4]} / 수행율 {rate}"})
    api_rate = calc_rate(api_status[2], api_status[1])
    area_fields.append({"type": "mrkdwn", "text": f"*API*\nPASS {api_status[3]} / FAIL {api_status[4]} / 수행율 {api_rate}"})

    total_rate = calc_rate(total_status[2], total_status[1])

    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📋 {project_name} | {today}"}
            },
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*📊 테스트 수행 현황*"}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*전체 TC*\n{total_status[1]}개"},
                    {"type": "mrkdwn", "text": f"*수행 TC*\n{total_status[2]}개"},
                    {"type": "mrkdwn", "text": f"*✅ PASS*\n{total_status[3]}개"},
                    {"type": "mrkdwn", "text": f"*❌ FAIL*\n{total_status[4]}개"},
                    {"type": "mrkdwn", "text": f"*🚫 BLOCK*\n{total_status[5]}개"},
                    {"type": "mrkdwn", "text": f"*수행율*\n{total_rate}"},
                ]
            },
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*📂 영역별 현황*"}},
            {"type": "section", "fields": area_fields},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*📅 테스트 일정*"}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*시작날짜*\n{start_date}"},
                    {"type": "mrkdwn", "text": f"*종료날짜*\n{end_date}"},
                ]
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"🔗 <https://docs.google.com/spreadsheets/d/{spreadsheet_id}|전체 리포트 보기>"}
                ]
            }
        ]
    }


def send_reports():
    print(f"[{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')}] 리포트 전송 시작...")
    try:
        client = get_gspread_client()
        projects = get_active_projects(client)

        if not projects:
            print("⚠️ 오늘 활성화된 프로젝트 없음")
            return

        for project in projects:
            print(f"  → [{project['name']}] 처리 중...")
            try:
                data = get_sheet_data(client, project["id"])
                message = build_slack_message(project["name"], data, project["start"], project["end"], project["id"])
                response = requests.post(SLACK_WEBHOOK_URL, json=message)
                if response.status_code == 200:
                    print(f"  ✅ [{project['name']}] 전송 성공!")
                else:
                    print(f"  ❌ [{project['name']}] 전송 실패: {response.status_code}")
            except Exception as e:
                print(f"  ❌ [{project['name']}] 오류: {e}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def main():
    print(f"🚀 QA 리포트 봇 시작 | 매일 {REPORT_TIME} 발송")
    schedule.every().day.at(REPORT_TIME).do(send_reports)

    send_reports()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
