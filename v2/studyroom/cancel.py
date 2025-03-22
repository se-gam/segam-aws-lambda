import json
import os
import sys

import bs4 as bs
import requests
import urllib3
from requests import Session
from urllib3.exceptions import InsecureRequestWarning

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.errors import PortalLoginError, SejongServerNotAvailableError
from auth.session import SejongPortalSession

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LIBRARY_LOGIN_URL = "http://library.sejong.ac.kr/sso/Login.ax"
LIBRARY_STUDYROOM_URL = "https://library.sejong.ac.kr/studyroom/Main.ax"
def cancel_reservation(id, password, booking_id, room_id, cancel_msg="잘못 예약"):
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
            _booking_id = x.find("a").get("href").split("'")[1]
            ipid = x.find("a").get("href").split("'")[3]
            room_id = x.find("a").get("href").split("'")[5]

            reservations.append(
                {
                    "booking_id": _booking_id,
                    "ipid": ipid,
                    "room_id": room_id,
                }
            )
    except AttributeError:
        return 400, "현재 스터디룸 예약 내역이 없습니다."

    if booking_id not in [x["booking_id"] for x in reservations]:
        return 404, "예약을 찾을 수 없습니다."

    sessionService.post(
        "https://library.sejong.ac.kr/studyroom/BookingProcess.axa",
        data={
            "cancelMsg": cancel_msg,
            "bookingId": booking_id,
            "expired": "C",
            "roomId": room_id,
            "mode": "update",
            "classId": "0",
        },
    )

    return 200, "예약이 취소되었습니다."


def lambda_handler(event, context):
    body = json.loads(event["body"])
    id = body["id"]
    password = body["password"]
    booking_id = body["booking_id"]
    room_id = body["room_id"]
    cancel_msg = body.get("cancel_msg", "잘못 예약")

    try:
        status_code, result = cancel_reservation(id, password, booking_id, room_id, cancel_msg)
        return {
            "statusCode": status_code,
            "body": json.dumps({"result": result}, ensure_ascii=False),
        }
    except (PortalLoginError, SejongServerNotAvailableError) as e:
        return {
            "statusCode": e.status_code,
            "body": json.dumps({"result": e.message}, ensure_ascii=False),
        }

