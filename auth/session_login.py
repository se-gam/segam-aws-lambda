import json
import bs4 as bs
import requests
import urllib3
from requests import Session

def login(id, password, max_retries=3, timeout=1):
    s = Session()

    headers = {
        "Host": "portal.sejong.ac.kr",
        "Referer": "https://portal.sejong.ac.kr"
    }

    cookies = {
        "chknos": "false",
    }

    data = {
        "mainLogin": "N",
        "rtUrl": "library.sejong.ac.kr",
        "id": id,
        "password": password,
    }

    url = "https://portal.sejong.ac.kr/jsp/login/login_action.jsp"

    for i in range(max_retries):
        try:
            r1 = s.post(
                url,
                headers=headers,
                cookies=cookies,
                data=data,
                timeout=timeout,
            )
            if "ssotoken" in r1.cookies:
                return r1.cookies
            break
        except requests.exceptions.Timeout:
            continue
        except requests.exceptions.RequestException as e:
            print(f"로그인 오류 발생: {e} 재시도...{i}")

    if not "ssotoken" in r1.cookies:
        return 401, "로그인 실패"