import json

import requests
import urllib3
from requests import Session
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def validate_user_availability(id, password, user_name, student_id, year, month, day):

    s = Session()

    headers = {
        "Host": "portal.sejong.ac.kr",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    cookies = {
        "chknos": "false",
    }

    url1 = "https://portal.sejong.ac.kr/jsp/login/loginSSL.jsp?rtUrl=portal.sejong.ac.kr/comm/member/user/ssoLoginProc.do"
    r1 = s.get(url1, headers=headers, verify=False)

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
        verify=False,
    )

    if "ssotoken" not in r2.cookies:
        return 401, {"error": "로그인 실패."}

    cookies["ssotoken"] = r2.cookies["ssotoken"]
    headers["Cookie"] = (
        f'chknos=false; WMONID={WMONID}; PO_JSESSIONID={PO_JSESSIONID}; PO1_JSESSIONID={PO1_JSESSIONID}; ssotoken={r2.cookies["ssotoken"]}'
    )

    url3 = "https://portal.sejong.ac.kr/user/index.do"
    s.get(url3, headers=headers, verify=False)

    url4 = "https://portal.sejong.ac.kr/comm/member/user/ssoLoginProc.do"
    s.get(url4, headers=headers, cookies=cookies, verify=False)

    url5 = "http://library.sejong.ac.kr/sso/Login.ax"
    s.get(url5, verify=False)

    url6 = "https://library.sejong.ac.kr/index.ax"
    s.get(url6, verify=False)

    url7 = "https://library.sejong.ac.kr/studyroom/Main.ax"
    r7 = s.get(url7, verify=False)

    r8 = s.post(
        "https://library.sejong.ac.kr/studyroom/UserFind.axa",
        {
            "altPid": student_id,
            "name": user_name,
            "userBlockUser": "Y",
            "year": year,
            "month": month,
            "day": day,
        },
        verify=False,
    )

    data = json.loads(r8.headers.get("X-JSON").replace("'", '"'))
    if data.get("result") == "true":
        return 200, {"ipid": data.get("ipid")}
    else:
        return 400, {"error": "예약이 불가능합니다."}


def lambda_handler(event, context):
    body = json.loads(event["body"])
    id = body["id"]
    password = body["password"]
    user_name = body["user_name"]
    student_id = body["student_id"]
    year = body["year"]
    month = body["month"]
    day = body["day"]

    code, result = validate_user_availability(
        id, password, user_name, student_id, year, month, day
    )

    return {"statusCode": code, "body": json.dumps(result, ensure_ascii=False)}
