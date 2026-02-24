# Lambda Layer 의존성 가이드

각 Lambda 함수별 필요 패키지와 추천 Layer 구성입니다.

## 필요 패키지 매트릭스

| 함수 | requests | urllib3 | bs4 | 비고 |
|------|----------|---------|-----|------|
| auth/session.py | ✅ | ✅ | ❌ | 포털 로그인 세션 관리 |
| auth/login.py | ✅ | ✅ | ✅ | 포털 로그인 + 사용자 정보 크롤링 |
| studyroom/cancel.py | ✅ | ✅ | ✅ | 예약 취소 |
| studyroom/my_reservation.py | ✅ | ✅ | ✅ | 내 예약 조회 |
| studyroom/reserve.py | ✅ | ✅ | ✅ | 예약 생성 |
| studyroom/validate_availability.py | ✅ | ✅ | ❌ | 예약 가능 여부 확인 |
| studyroom/calendar.py | ✅ | ✅ | ✅ | 주간 예약 현황 조회 |

## 추천 Layer 구성

### Layer 1: `requests-layer`
- **패키지**: `requests`, `urllib3`, `charset-normalizer`, `idna`, `certifi`
- **사용 함수**: 전체 (모든 함수에서 사용)

### Layer 2: `bs4-layer`
- **패키지**: `beautifulsoup4`, `soupsieve`
- **사용 함수**: auth/login, studyroom/cancel, my_reservation, reserve, calendar

## Layer 빌드 방법

```bash
# requests-layer
mkdir -p layer/python
pip install requests -t layer/python/
cd layer && zip -r ../requests-layer.zip python/

# bs4-layer
mkdir -p layer/python
pip install beautifulsoup4 -t layer/python/
cd layer && zip -r ../bs4-layer.zip python/
```

## 함수별 Layer 매핑

| 함수 | 필요 Layer |
|------|-----------|
| auth/session.py | requests-layer |
| auth/login.py | requests-layer + bs4-layer |
| studyroom/cancel.py | requests-layer + bs4-layer |
| studyroom/my_reservation.py | requests-layer + bs4-layer |
| studyroom/reserve.py | requests-layer + bs4-layer |
| studyroom/validate_availability.py | requests-layer |
| studyroom/calendar.py | requests-layer + bs4-layer |

## 참고

- Python 3.14 런타임 대상
- `pandas` 의존성 완전 제거 (calendar.py에서 bs4로 대체)
- `sejong_univ_auth` 의존성 완전 제거 (login.py에서 SejongPortalSession으로 대체)
- `sys.path.append` 패턴 제거 — 패키지 상대 import 사용
