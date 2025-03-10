import json

import requests

LOGIN_API_ROOT = "http://classic.sejong.ac.kr/userLogin.do"
MONTHLY_CHECK_TABLE_API_ROOT = (
    "http://classic.sejong.ac.kr/schedulePageList.do?menuInfoId=MAIN_02_04"
)
USER_RESERVATION_STATUS_API_ROOT = (
    "https://classic.sejong.ac.kr/viewUserAppInfo.do?menuInfoId=MAIN_02_04"
)
CANCLE_API_ROOT = "https://classic.sejong.ac.kr/cencelSchedule.do?menuInfoId=MAIN_02_04"
RESERVE_API_ROOT = "https://classic.sejong.ac.kr/addAppInfo.do?menuInfoId=MAIN_02_04"
SELECT_BOOT_TERMLIST_API_ROOT = "https://classic.sejong.ac.kr/seletTermBookList.json"
RESERVE_CHECK_API_ROOT = (
    "https://classic.sejong.ac.kr/addUserSchedule.do?menuInfoId=MAIN_02"
)


def cancel(id, password, opAppInfoId):
    payload = {"userId": id, "password": password, "go": ""}
    session = requests.Session()
    response = session.post(LOGIN_API_ROOT, data=payload)

    if response.history:
        payload = {"opAppInfoId": opAppInfoId}
        response = session.post(CANCLE_API_ROOT, data=payload)
        if response.history:
            return "취소 성공"
        else:
            return "취소 실패"
    return "로그인 실패"


def lambda_handler(event, context):
    try:
        event = json.loads(event["body"])
        student_id = event["student_id"]
        password = event["password"]
        opAppInfoId = event["opAppInfoId"]

        response = cancel(student_id, password, opAppInfoId)

        if response == "로그인 실패":
            status_code = 401
        elif response == "취소 성공":
            status_code = 200
        else:
            status_code = 400
        return {
            "statusCode": status_code,
            "headers": {},
            "body": json.dumps(
                {
                    "message": response,
                },
                ensure_ascii=False,
            ),
        }
    except KeyError:
        return {
            "statusCode": 400,
            "headers": {},
            "body": json.dumps(
                {
                    "message": "Invalid student_id or password",
                }
            ),
        }
