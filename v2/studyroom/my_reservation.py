import sys
import os
import json

import bs4 as bs
import requests

import urllib3
from urllib3.exceptions import InsecureRequestWarning


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.errors import PortalLoginError, SejongServerNotAvailableError
from auth.session import SejongPortalSession

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LIBRARY_LOGIN_URL = "http://library.sejong.ac.kr/sso/Login.ax"
LIBRARY_STUDYROOM_URL = "https://library.sejong.ac.kr/studyroom/Main.ax"

def get_my_reservations(id, password):
    sessionService = SejongPortalSession(id, password)
    sessionService.get(LIBRARY_LOGIN_URL)
    r = sessionService.get(LIBRARY_STUDYROOM_URL)
    reservations = []

    try:
        for x in (
            bs.BeautifulSoup(r.text, "html.parser")
            .find_all("table", {"class": "tb01 width-full"})[-1]
            .find_all("tr")[1:]
        ):
            booking_id = x.find("a").get("href").split("'")[1]
            ipid = x.find("a").get("href").split("'")[3]
            room_id = x.find("a").get("href").split("'")[5]

            reservations.append(
                {
                    "booking_id": booking_id,
                    "ipid": ipid,
                    "room_id": room_id,
                }
            )
    except AttributeError:
        return 404, "예약 내역이 없습니다."
    
    result = []

    for reservation in reservations:
        r4 = sessionService.post(
            "https://library.sejong.ac.kr/studyroom/BookingDetail.axa",
            data={
                "bookingId": reservation["booking_id"],
                "ipid": reservation["ipid"],
                "roomId": reservation["room_id"],
            },
        )

        tmp = {
            "booking_id": reservation["booking_id"],
            "ipid": reservation["ipid"],
            "room_id": reservation["room_id"],
        }

        for x in (
            bs.BeautifulSoup(r4.text, "html.parser")
            .find_all("table", {"class": "tb03 width-100"})[0]
            .find_all("tr")[2:]
        ):
            if x.find("th").text.strip() == "이용시간":
                tmp["duration"] = x.find("td").text.strip().split("부터")[1]
                _date, _time = (
                    x.find("td").text.strip().split("부터")[0].strip().split(" ")
                )
                tmp["date"] = _date
                tmp["starts_at"] = _time
            elif x.find("th").text.strip() == "동반 사용자":
                raw_users = [
                    _.strip().split(":") for _ in x.find("td").text.strip().split("\n")
                ]
                users = []
                for user in raw_users:
                    users.append(
                        {
                            "name": user[0].strip(),
                            "student_id": user[1].split("/")[0].strip(),
                        }
                    )
                tmp["users"] = users
            elif x.find("th").text.strip() == "사용목적":
                tmp["purpose"] = x.find("td").text.strip()

        if tmp not in result:
            result.append(tmp)

    return 200, result

def lambda_handler(event, context):
    body = json.loads(event["body"])
    id = body["student_id"]
    password = body["password"]

    try:
        status_code, result = get_my_reservations(id, password)
        return {
            "statusCode": status_code,
            "body": json.dumps({"result": result}, ensure_ascii=False),
        }
    except (PortalLoginError, SejongServerNotAvailableError) as e:
        return {
            "statusCode": e.status_code,
            "body": json.dumps({"result": e.message}, ensure_ascii=False),
        }
