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

    r2 = s.post(
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

    data = json.loads(r2.headers.get("X-JSON").replace("'", '"'))
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
