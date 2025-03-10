import datetime
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


def get_my_reservation(student_id, password):
    payload = {"userId": student_id, "password": password, "go": ""}
    session = requests.Session()
    response = session.post(LOGIN_API_ROOT, data=payload)

    if response.history:
        response = session.post(USER_RESERVATION_STATUS_API_ROOT)

        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find_all("tbody")
        tr_elements = table[0].select("tr")
        if (
            tr_elements[0].select_one("td:nth-child(1)").text.strip()
            == "검색된 결과가 없습니다."
        ):
            return []
        result = []
        for data in tr_elements:
            date = data.select_one("td:nth-child(2)").text.strip()
            time = data.select_one("td:nth-child(3)").text.split("~")[0].strip()
            book_name = data.select_one("td:nth-child(5)").text.strip()
            reserve_id = str(data.select_one("td:nth-child(6)").select("button"))
            start_index = reserve_id.find("(")
            end_index = reserve_id.find(")")
            reserve_id = reserve_id[start_index + 2 : end_index - 1]

            dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            iso_string = dt.isoformat()

            reserve_data = {
                "date_time": iso_string + "+09:00",
                "book_name": book_name,
                "reserve_id": reserve_id,
            }
            result.append(reserve_data)
        return result
    else:
        print("로그인 실패")


def lambda_handler(event, context):
    try:
        event = json.loads(event["body"])
        student_id = event["student_id"]
        password = event["password"]

        response = get_my_reservation(student_id, password)

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
