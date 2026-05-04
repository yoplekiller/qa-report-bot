# QA Daily Report Bot

## 프로젝트 개요
프로젝트 테스트 케이스 수행 시 수행율 체크 및 보고의 자동화를 위해 해당 포트폴리오를 작성했습니다.
기존에 수동으로 집계하던 테스트 수행율을 Google Sheets와 Slack을 연동하여 매일 자동으로 보고되도록 구현했습니다.

## 주요 기능
- Google Sheets 테스트 수행율 데이터 자동 읽기
- 마스터 시트 기반 멀티 프로젝트 관리
- 프로젝트별 테스트 기간(시작일/종료일) 설정 및 자동 활성화/비활성화
- 수행TC / 전체TC 기반 수행율 자동 계산
- Slack Block Kit 리포트 자동 발송
- GitHub Actions를 통한 매일 17:00 KST 자동 실행
- 시트 구성 변경 시 코드 수정 없이 자동 반영

## 기술 스택
| 분류 | 기술 |
|------|------|
| Language | Python 3.11 |
| API | Google Sheets API, Slack Incoming Webhooks |
| 라이브러리 | gspread, google-auth, requests, schedule |
| 자동화 | GitHub Actions |
| 데이터 | Google Sheets |
| 협업/배포 | GitHub |

## 시스템 아키텍처
마스터 시트 (QA 리포트 관리)
└── 프로젝트명 / 시트URL / 시작일 / 종료일
        ↓ 날짜 범위 체크 (오늘 날짜 기준 활성 프로젝트 필터링)
수행율 시트 (프로젝트별 Google Sheets)
└── 테스트 수행 현황 / 영역별 현황
        ↓ 수행율 자동 계산 (수행TC / 전체TC)
Slack Block Kit 리포트 생성
        ↓
GitHub Actions 스케줄러 (매일 17:00 KST 자동 실행)
        ↓
Slack 채널 자동 발송

## 실행 화면

### Slack 리포트 알림
![Slack 리포트](docs/images/slack_report.png)

### 마스터 시트 (프로젝트 관리)
![마스터 시트](docs/images/master_sheet.png)

### 수행율 시트 (프로젝트별)
![수행율 시트](docs/images/execution_sheet.png)

### GitHub Actions 실행 로그
![Actions 로그](docs/images/actions_log.png)

## 설치 및 실행 방법

### 사전 준비

1. **Google Cloud 서비스 계정 생성**
   - [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
   - Google Sheets API 활성화
   - 서비스 계정 생성 후 JSON 키 파일 다운로드
   - 마스터 시트와 수행율 시트에 서비스 계정 이메일을 편집자로 공유

2. **Slack Incoming Webhook 생성**
   - Slack 앱 설정에서 Incoming Webhooks 활성화
   - 채널 선택 후 Webhook URL 복사

3. **Google Sheets 구성**
   - 마스터 시트: `프로젝트명 | 시트URL | 시작일(YYYY-MM-DD) | 종료일(YYYY-MM-DD)` 형식으로 작성
   - 수행율 시트: `영역 | 전체TC | 수행TC` 형식으로 작성

### 로컬 실행

```bash
# 의존성 설치
pip install gspread google-auth schedule requests

# 서비스 계정 JSON 파일을 프로젝트 루트에 배치
# config.py에서 CREDS_FILE, MASTER_SPREADSHEET_ID 설정

# 환경변수 설정
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# 즉시 실행
python -c "from report_bot import send_reports; send_reports()"
```

### GitHub Actions 자동화

1. 레포지토리 Settings → Secrets and variables → Actions에서 시크릿 추가:
   - `GOOGLE_CREDENTIALS`: 서비스 계정 JSON 파일 전체 내용
   - `SLACK_WEBHOOK_URL`: Slack Webhook URL

2. `.github/workflows/report.yml`이 매일 17:00 KST (08:00 UTC)에 자동 실행

3. 수동 실행: Actions 탭 → QA Daily Report → Run workflow

## 파일 구조

```
qa-report-bot/
├── .github/
│   └── workflows/
│       └── report.yml        # GitHub Actions 스케줄러
├── docs/
│   ├── images/               # 실행 화면 캡처 이미지
│   └── development-log.md    # 개발 일지
├── config.py                 # 설정값 (시트 ID, 인증 파일명 등)
├── report_bot.py             # 메인 봇 (시트 읽기 + Slack 발송)
├── check_master.py           # 마스터 시트 디버그용
├── check_sheet.py            # 수행율 시트 디버그용
├── debug.py                  # 통합 디버그용
├── requirements.txt          # 의존성 목록 (Actions에서 자동 설치)
└── README.md
```