import json

import bs4 as bs
import requests
import urllib3
from requests import Session
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_my_reservations(id, password):
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

        r4 = s.post(
            "https://library.sejong.ac.kr/studyroom/BookingDetail.axa",
            data={
                "bookingId": reservations[0]["booking_id"],
                "ipid": reservations[0]["ipid"],
                "roomId": reservations[0]["room_id"],
            },
            verify=False,
        )
    except AttributeError:
        return 404, "예약 내역이 없습니다."

    result = []

    for reservation in reservations:
        r4 = s.post(
            "https://library.sejong.ac.kr/studyroom/BookingDetail.axa",
            data={
                "bookingId": reservation["booking_id"],
                "ipid": reservation["ipid"],
                "roomId": reservation["room_id"],
            },
            verify=False,
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

    code, result = get_my_reservations(id, password)

    return {
        "statusCode": code,
        "body": json.dumps({"result": result}, ensure_ascii=False),
    }
