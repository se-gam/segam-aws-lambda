import json

import bs4 as bs
import requests
import urllib3
from requests import Session
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def create_reservation(
    id, password, room_id, users, year, month, day, start_time, hours, purpose="공부"
):

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

    url3 = "https://library.sejong.ac.kr/studyroom/Request.ax?roomId=" + str(room_id)
    r3 = s.get(url3, verify=False)

    soup = bs.BeautifulSoup(r3.text, "html.parser")

    data = {}

    for x in soup.find("form", {"id": "frmMain"}).find_all("input"):
        if x.get("name"):
            data[x["name"]] = x.get("value") if x.get("value") else ""

    for i, user in enumerate(users):
        data[f"altPid{i+1}"] = user["student_id"]
        data[f"name{i+1}"] = user["name"]
        data[f"ipid{i+1}"] = user["ipid"]

    data["year"] = year
    data["month"] = month
    data["day"] = day
    data["startHour"] = start_time
    data["closeTime"] = "22"
    data["hours"] = hours
    data["purpose"] = purpose
    data["mode"] = "INSERT"

    # print(data)

    r4 = s.post(
        "https://library.sejong.ac.kr/studyroom/BookingProcess.axa",
        data=data,
        verify=False,
    )

    if "true" in r4.headers.get("X-JSON"):
        return 200, {"result": "예약이 완료되었습니다."}
    else:
        return 400, {"error": r4.text.strip()}


def lambda_handler(event, context):
    body = json.loads(event["body"])
    id = body["id"]
    password = body["password"]
    room_id = body["room_id"]
    users = body["users"]
    year = body["year"]
    month = body["month"]
    day = body["day"]
    start_time = body["start_time"]
    hours = body["hours"]
    purpose = body.get("purpose", "스터디")

    code, result = create_reservation(
        id, password, room_id, users, year, month, day, start_time, hours, purpose
    )

    return {"statusCode": code, "body": json.dumps(result, ensure_ascii=False)}
