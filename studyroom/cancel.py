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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    cookies = {
        "chknos": "false",
    }

    url1 = "https://portal.sejong.ac.kr/jsp/login/loginSSL.jsp?rtUrl=portal.sejong.ac.kr/comm/member/user/ssoLoginProc.do"
    r1 = s.get(url1, headers=headers)

    WMONID = r1.cookies["WMONID"]
    PO_JSESSIONID = r1.cookies["PO_JSESSIONID"]
    PO1_JSESSIONID = r1.cookies["PO1_JSESSIONID"]

    cookies["WMONID"] = WMONID
    cookies["PO_JSESSIONID"] = PO_JSESSIONID
    cookies["PO1_JSESSIONID"] = PO1_JSESSIONID
    headers["Referer"] = (
        "https://portal.sejong.ac.kr/jsp/login/loginSSL.jsp?rtUrl=portal.sejong.ac.kr/comm/member/user/ssoLoginProc.do"
    )
    headers["Cookie"] = (
        f"chknos=false; WMONID={WMONID}; PO_JSESSIONID={PO_JSESSIONID}; PO1_JSESSIONID={PO1_JSESSIONID}"
    )

    url2 = "https://portal.sejong.ac.kr/jsp/login/login_action.jsp"
    r2 = s.post(
        url2,
        headers=headers,
        cookies=cookies,
        data={
            "mainLogin": "Y",
            "rtUrl": "portal.sejong.ac.kr/comm/member/user/ssoLoginProc.do",
            "id": id,
            "password": password,
        },
    )

    if "ssotoken" not in r2.cookies:
        return 401, "로그인 실패"

    cookies["ssotoken"] = r2.cookies["ssotoken"]
    headers["Cookie"] = (
        f'chknos=false; WMONID={WMONID}; PO_JSESSIONID={PO_JSESSIONID}; PO1_JSESSIONID={PO1_JSESSIONID}; ssotoken={r2.cookies["ssotoken"]}'
    )

    url3 = "https://portal.sejong.ac.kr/user/index.do"
    s.get(url3, headers=headers)

    url4 = "https://portal.sejong.ac.kr/comm/member/user/ssoLoginProc.do"
    s.get(url4, headers=headers, cookies=cookies)

    url5 = "http://library.sejong.ac.kr/sso/Login.ax"
    s.get(url5, verify=False)

    url6 = "https://library.sejong.ac.kr/index.ax"
    s.get(url6, verify=False)

    url7 = "https://library.sejong.ac.kr/studyroom/Main.ax"
    r7 = s.get(url7, verify=False)

    reservations = []

    try:
        for x in (
            bs.BeautifulSoup(r7.text, "html.parser")
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

    r8 = s.post(
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
