import requests
import urllib3
from requests import Session
from urllib3.exceptions import InsecureRequestWarning

from .errors import PortalLoginError, SejongServerNotAvailableError

urllib3.disable_warnings(InsecureRequestWarning)
class SejongPortalSession:
    PORTAL_AUTH_URL = "https://portal.sejong.ac.kr/jsp/login/login_action.jsp"
    MAX_RETRIES = 3
    LOGIN_HEADERS = {
        "Host": "portal.sejong.ac.kr",
        "Referer": "https://portal.sejong.ac.kr"
    }
    LOGIN_COOKIES = {
        "chknos": "false",
    }

    def __init__(self, id, password):
        self.session = Session()
        self.login(id, password)

    def get(self, url, **kwargs):
        for i in range(self.MAX_RETRIES):
            try:
                return self.session.get(url, **kwargs, timeout=0.4, verify=False)
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.RequestException as e:
                print(f"요청 오류 발생: {e} 재시도...{i+1}")
        raise SejongServerNotAvailableError
        
    def post(self, url, **kwargs):
        for i in range(self.MAX_RETRIES):
            try:
                return self.session.post(url, **kwargs, timeout=0.4, verify=False)
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.RequestException as e:
                print(f"요청 오류 발생: {e} 재시도...{i+1}")
        raise SejongServerNotAvailableError

    def library_login(self):
        """도서관 SSO 로그인"""
        self.get("http://library.sejong.ac.kr/sso/Login.ax")

    def login(self, id, password):
        data = {
            "mainLogin": "N",
            "id": id,
            "password": password,
        }

        for i in range(self.MAX_RETRIES):
            try:
                print(f"로그인 시도 {i+1}번째")
                r1 = self.session.post(
                    self.PORTAL_AUTH_URL,
                    headers=self.LOGIN_HEADERS,
                    cookies=self.LOGIN_COOKIES,
                    data=data,
                    timeout=0.2,
                )
                if "ssotoken" in r1.cookies:
                    return
                else:
                    if "result = 'pwdNeedChg'" in r1.text:
                        raise PortalLoginError(401, "일정 횟수 이상 패스워드를 잘못 입력하여 계정이 잠겼습니다. 비밀번호 찾기 페이지에서 비밀번호를 재설정하셔야 합니다.")
                    elif "result = 'erridpwd'" in r1.text:
                        raise PortalLoginError(401, "아이디나 비밀번호가 일치하지 않습니다.")
                    elif "result = 'invalidDt'" in r1.text:
                        raise PortalLoginError(401, "계정의 사용 허용기간이 종료되었습니다. sj로 시작하는 아이디, 원직번, 성명, 소속부서, 사용사유를 itservice@sejong.ac.kr로 보내주시기 바랍니다. 내용에 따라 사용권한 요청서가 추가로 필요할 수 있습니다.")
                    elif "result = 'Error'" in r1.text:
                        raise PortalLoginError(401, "아이디나 비밀번호가 일치하지 않습니다.")
                    elif "result = 'invalid'" in r1.text:
                        raise PortalLoginError(401, "이 계정은 계정관리자의 요청으로 현재 로그인이 불가 합니다.")
                    else:
                        raise PortalLoginError(401, "로그인 처리 중 오류가 발생하였습니다.")
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.RequestException as e:
                print(f"로그인 오류 발생: {e} 재시도...{i+1}")
        raise SejongServerNotAvailableError
