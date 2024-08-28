import json
import re

import requests
from bs4 import BeautifulSoup

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


def reserve(id, password, shInfoId, bkCode, bkAreaCode):
    payload = {"userId": id, "password": password, "go": ""}
    session = requests.Session()
    response = session.post(LOGIN_API_ROOT, data=payload)

    if response.history:
        response = session.get(RESERVE_CHECK_API_ROOT + "&shInfoId=" + shInfoId)
        if response.history:
            alert_re = r"alert\((.*)\)"
            alert = re.findall(alert_re, response.text)
            error = alert[-1].replace('"', "").strip()
            return error if error else "예약 실패"
        soup = BeautifulSoup(response.text, "html.parser")
        opTermId = soup.find("input", {"id": "opTermId"}).get("value")

        data = {
            "shInfoId": shInfoId,
            "opTermId": opTermId,
            "bkCode": bkCode,
            "bkAreaCode": bkAreaCode,
        }
        response = session.post(RESERVE_API_ROOT, data=data)

        return "예약 성공"
    else:
        return "로그인 실패"


def lambda_handler(event, context):
    try:
        event = json.loads(event["body"])
        student_id = event["student_id"]
        password = event["password"]
        shInfoId = event["shInfoId"]
        bkCode = event["bkCode"]
        bkAreaCode = event["bkAreaCode"]

        response = reserve(student_id, password, shInfoId, bkCode, bkAreaCode)

        if response == "로그인 실패":
            status_code = 401
        elif response == "예약 성공":
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
