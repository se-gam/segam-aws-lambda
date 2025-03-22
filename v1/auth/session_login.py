import requests
from requests import Session

class CustomSession:
    def __init__(self, session=None, headers=None, cookies=None):
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.session = session or Session()

    def login(self, id, password, max_retries=3, timeout=1):
        data = {
            "mainLogin": "N",
            "rtUrl": "library.sejong.ac.kr",
            "id": id,
            "password": password,
        }

        url = "https://portal.sejong.ac.kr/jsp/login/login_action.jsp"

        for i in range(max_retries):
            try:
                r1 = self.session.post(
                    url,
                    headers=self.headers,
                    cookies=self.cookies,
                    data=data,
                    timeout=timeout,
                )
                if "ssotoken" in r1.cookies:
                    self.cookies["ssotoken"] = r1.cookies["ssotoken"]
                    self.headers["Cookie"] = f"chknos=false;"
                return
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.RequestException as e:
                print(f"로그인 오류 발생: {e} 재시도...{i+1}")
        raise RuntimeError("로그인 실패")
