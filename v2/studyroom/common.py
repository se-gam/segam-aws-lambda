import json

from ..auth.errors import PortalLoginError, SejongServerNotAvailableError

LIBRARY_LOGIN_URL = "http://library.sejong.ac.kr/sso/Login.ax"
LIBRARY_STUDYROOM_URL = "https://library.sejong.ac.kr/studyroom/Main.ax"
STUDYROOM_RESERVE_URL = "https://library.sejong.ac.kr/studyroom/Request.ax?roomId="
STUDYROOM_BOOKING_PROCESS_URL = "https://library.sejong.ac.kr/studyroom/BookingProcess.axa"
LIBRARY_USER_FIND_URL = "https://library.sejong.ac.kr/studyroom/UserFind.axa"
STUDYROOM_BOOKING_DETAIL_URL = "https://library.sejong.ac.kr/studyroom/BookingDetail.axa"
STUDYROOM_BOOKING_TABLE_URL = "https://library.sejong.ac.kr/studyroom/BookingTable.axa"


def make_lambda_handler(func, body_keys):
    """공통 lambda_handler 래퍼.

    Args:
        func: 비즈니스 로직 함수 (status_code, result) 튜플 반환
        body_keys: event["body"]에서 추출할 키 리스트.
                   "key" → 필수, "key?" → 선택(기본값 None), "key?=default" → 선택(기본값 지정)
    """
    def handler(event, context):
        body = json.loads(event["body"])
        args = []
        for key in body_keys:
            if "?=" in key:
                name, default = key.split("?=", 1)
                args.append(body.get(name, default))
            elif key.endswith("?"):
                args.append(body.get(key[:-1]))
            else:
                args.append(body[key])

        try:
            status_code, result = func(*args)
            return {
                "statusCode": status_code,
                "body": json.dumps({"result": result}, ensure_ascii=False),
            }
        except (PortalLoginError, SejongServerNotAvailableError) as e:
            return {
                "statusCode": e.status_code,
                "body": json.dumps({"result": e.message}, ensure_ascii=False),
            }

    return handler
