# QA Report Bot 개발 로그

## 개요
Google Sheets에 기록된 QA 테스트 수행율 데이터를 읽어 매일 정해진 시간에 Slack으로 자동 발송하는 봇.
마스터 시트로 멀티 프로젝트를 관리하며, GitHub Actions로 PC 없이 자동 실행된다.

---

## 전체 아키텍처

```
마스터 시트 (QA 리포트 관리)
  └── 프로젝트명 / 시트URL / 시작일 / 종료일
        ↓ 날짜 범위 체크
수행율 시트 (프로젝트별)
  └── 테스트 수행 현황 / 영역별 현황
        ↓ 파싱 및 계산
Slack Block Kit 메시지 생성
        ↓
GitHub Actions 스케줄러 (매일 17:00 KST)
```

---

## 구현 순서

### 1단계: Google Cloud 설정
- Google Cloud Console에서 프로젝트 생성 (`qa-report-bot`)
- Google Sheets API 활성화
- 서비스 계정 생성 및 JSON 키 발급
- 수행율 시트 / 마스터 시트에 서비스 계정 이메일 공유 (뷰어 권한)

### 2단계: 패키지 설치
```bash
pip install gspread google-auth schedule requests
```

### 3단계: 마스터 시트 구조
| 프로젝트명 | 시트URL | 시작일 | 종료일 |
|-----------|--------|--------|--------|
| 마켓컬리 UI_TMDB API 테스트 | https://... | 2026-05-01 | 2026-05-31 |

- 시작일/종료일 **둘 다** 입력된 경우에만 활성화 (안전장치)
- 날짜 범위 벗어나면 자동 스킵 (코드 수정 불필요)
- 새 프로젝트 추가 = 행 하나만 추가하면 끝

### 4단계: 수행율 시트 구조
```
Row 0: 프로젝트명 (헤더 타이틀)
Row 1: 구분 / 총TC / 수행TC / PASS / FAIL / BLOCK / N/A / 수행율 / 통과율 / 실패율
Row 2~4: 영역별 데이터 (마켓컬리_TC, API_TC, 전체)
```

### 5단계: 핵심 로직

**수행율 직접 계산**
시트의 수행율 공식이 `PASS/수행TC` (통과율 공식)로 잘못 입력되어 있어,
코드에서 `수행TC / 전체TC`로 직접 계산하도록 처리.

```python
def calc_rate(numerator, denominator):
    n, d = int(numerator), int(denominator)
    if d == 0:
        return "0%"
    return f"{round(n / d * 100)}%"
```

**영역 키 동적 추출**
시트에 영역이 추가되어도 코드 수정 없이 자동 반영.
```python
area_keys = [k for k in status_rows if k not in ("전체", "API_TC")]
```

**URL에서 Spreadsheet ID 추출**
마스터 시트에 전체 URL을 입력해도 ID만 파싱해서 사용.
```python
def extract_spreadsheet_id(url):
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None
```

### 6단계: Slack Block Kit 메시지 구조
```
📋 [프로젝트명] | [날짜]
────────────────
📊 테스트 수행 현황
  전체TC / 수행TC / PASS / FAIL / BLOCK / 수행율
────────────────
📂 영역별 현황
  영역1: PASS / FAIL / 수행율
  API: PASS / FAIL / 수행율
────────────────
📅 테스트 일정
  시작날짜 / 종료날짜
────────────────
🔗 전체 리포트 보기
```

### 7단계: GitHub Actions 설정

**워크플로우 트리거**
- 매일 08:00 UTC (= 17:00 KST) 자동 실행
- `workflow_dispatch`로 수동 실행 버튼 제공

**Secrets 관리 (보안)**
- `GOOGLE_CREDENTIALS`: JSON 키 파일 전체 내용
- `SLACK_WEBHOOK_URL`: Slack Webhook URL
- JSON 키 파일은 `.gitignore`로 GitHub 업로드 차단

**실행 방식**
GitHub Actions에서는 `schedule` 루프 없이 `send_reports()`만 직접 호출.
```yaml
run: python -c "from report_bot import send_reports; send_reports()"
```

---

## 트러블슈팅

### 한국어 키 매칭 실패
- **증상**: 영역별 현황이 `-`로 표시
- **원인**: 시트 키가 `트래블링_TC`가 아닌 `마켓컬리_TC`였음
- **해결**: 하드코딩 제거 → 동적 키 추출 방식으로 변경

### Windows 터미널 이모지 인코딩 오류
- **증상**: `UnicodeEncodeError: 'cp949' codec can't encode character`
- **원인**: Windows 기본 터미널이 cp949 인코딩 사용
- **해결**: `sys.stdout.reconfigure(encoding='utf-8')` 추가

### 수행율 100% 오류
- **증상**: 수행율이 비정상적으로 100%로 표시
- **원인**: 시트 공식이 `PASS/수행TC`로 계산 (통과율 공식)
- **해결**: 코드에서 `수행TC/전체TC`로 직접 계산

### context 블록 링크 중복
- **증상**: 전체 리포트 보기 링크가 두 번 표시
- **원인**: post-build 덮어쓰기 시 인덱스 오류로 날짜 요소를 링크로 덮어씀
- **해결**: spreadsheet_id를 build_slack_message에 직접 파라미터로 전달

---

## 파일 구조
```
qa-report-bot/
├── .github/
│   └── workflows/
│       └── report.yml       # GitHub Actions 스케줄러
├── docs/
│   └── development-log.md   # 개발 로그 (현재 파일)
├── config.py                # 설정값 (ID, URL, 시간)
├── report_bot.py            # 메인 봇 로직
├── check_sheet.py           # 시트 데이터 확인용 (개발용)
├── check_master.py          # 마스터 시트 확인용 (개발용)
├── debug.py                 # 키 인코딩 디버그용 (개발용)
├── .gitignore               # JSON 키 파일 제외
└── qa-report-bot-*.json     # Google 서비스 계정 키 (gitignore)
```
