import json

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
MY_STATUS_API_ROOT = (
    "http://classic.sejong.ac.kr/userCertStatus.do?menuInfoId=MAIN_02_05"
)


def get_my_status(student_id, password):
    payload = {"userId": student_id, "password": password, "go": ""}
    session = requests.Session()
    response = session.post(LOGIN_API_ROOT, data=payload)

    if response.history:
        response = session.post(MY_STATUS_API_ROOT)

        soup = BeautifulSoup(response.text, "html.parser")

        status_soup = soup.select_one("ul.tblA").select("li")[-1].get_text().strip()

        status = True
        if "대체이수" in status_soup:
            status = True
        elif "아니오" in status_soup:
            status = False

        values_soup = soup.select_one("table.listA").select("tbody > tr > td")
        values = {
            (i + 1) * 1000: v
            for i, v in enumerate(
                [int(x.get_text().split()[0]) for x in values_soup[7:11]]
            )
        }
        return {
            "status": status,
            "values": values,
        }

    else:
        print("로그인 실패")


def lambda_handler(event, context):
    try:
        event = json.loads(event["body"])
        student_id = event["student_id"]
        password = event["password"]

        response = get_my_status(student_id, password)

        if response == "로그인 실패":
            status_code = 401
        else:
            status_code = 200
        return {
            "statusCode": status_code,
            "headers": {},
            "body": json.dumps(
                {
                    "reservations": response,
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
