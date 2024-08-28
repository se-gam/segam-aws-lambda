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

    url8 = "https://library.sejong.ac.kr/studyroom/Request.ax?roomId=" + str(room_id)
    r8 = s.get(url8, verify=False)

    soup = bs.BeautifulSoup(r8.text, "html.parser")

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

    r9 = s.post(
        "https://library.sejong.ac.kr/studyroom/BookingProcess.axa",
        data=data,
        verify=False,
    )

    print(r9.headers)
    print(r9.text)

    if "true" in r9.headers.get("X-JSON"):
        return 200, {"result": "예약이 완료되었습니다."}
    else:
        return 400, {"error": r9.text.strip()}


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
