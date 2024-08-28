import json

import bs4 as bs
import requests
import urllib3
from requests import Session
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def cancel_reservation(id, password, booking_id, room_id, cancel_msg="잘못 예약"):
    s = Session()

    headers = {
        "Host": "portal.sejong.ac.kr",
    }

    cookies = {
        "chknos": "false",
    }

    headers["Referer"] = "https://portal.sejong.ac.kr"

    url1 = "https://portal.sejong.ac.kr/jsp/login/login_action.jsp"

    while True:
        try:
            r1 = s.post(
                url1,
                headers=headers,
                cookies=cookies,
                data={
                    "mainLogin": "N",
                    "rtUrl": "library.sejong.ac.kr",
                    "id": id,
                    "password": password,
                },
                timeout=0.2,
            )
            break
        except requests.exceptions.Timeout:
            pass

    if not "ssotoken" in r1.cookies:
        return 401, "로그인 실패"

    cookies["ssotoken"] = r1.cookies["ssotoken"]
    headers["Cookie"] = f"chknos=false;"

    url2 = "http://library.sejong.ac.kr/sso/Login.ax"
    s.get(url2, verify=False)

    url3 = "https://library.sejong.ac.kr/studyroom/Main.ax"
    r3 = s.get(url3, verify=False)

    reservations = []

    try:
        for x in (
            bs.BeautifulSoup(r3.text, "html.parser")
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

    r4 = s.post(
        "https://library.sejong.ac.kr/studyroom/BookingProcess.axa",
        {
            "cancelMsg": cancel_msg,
            "bookingId": booking_id,
            "expired": "C",
            "roomId": room_id,
            "mode": "update",
            "classId": "0",
        },
        verify=False,
    )

    return 200, "예약이 취소되었습니다."


def lambda_handler(event, context):
    body = json.loads(event["body"])
    id = body["id"]
    password = body["password"]
    booking_id = body["booking_id"]
    room_id = body["room_id"]
    cancel_msg = body.get("cancel_msg", "잘못 예약")

    code, result = cancel_reservation(id, password, booking_id, room_id, cancel_msg)

    return {
        "statusCode": code,
        "body": json.dumps({"result": result}, ensure_ascii=False),
    }
