import re

import requests
import urllib3
from requests import Session
from urllib3.exceptions import InsecureRequestWarning

from .errors import PortalLoginError, SejongServerNotAvailableError

urllib3.disable_warnings(InsecureRequestWarning)


class SejongPortalSession:
    PORTAL_LOGIN_SSL = "https://portal.sejong.ac.kr/jsp/login/loginSSL.jsp"
    PORTAL_AUTH_URL = "https://portal.sejong.ac.kr/jsp/login/login_action.jsp"
    PORTAL_SSO_PROC = "http://portal.sejong.ac.kr/comm/member/user/ssoLoginProc.do"
    LIBRARY_LOGIN = "https://library.sejong.ac.kr/login"
    LIBRARY_ROOT_HTTP = "http://library.sejong.ac.kr/"
    LIBRARY_STUDYROOM_REL = "https://library.sejong.ac.kr/relation/studyroom"
    LIBSEAT_CHECKING_URL = "https://libseat.sejong.ac.kr/mobile/MA/mySeat.php"
    PORTAL_LOGIN_ACTION = "https://portal.sejong.ac.kr/jsp/login/login_action.jsp"
    LIBRARY_REL = "https://library.sejong.ac.kr/relation/studyroom"

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    MAX_RETRIES = 3
    LOGIN_HEADERS = {
        "Host": "portal.sejong.ac.kr",
        "Referer": "https://portal.sejong.ac.kr",
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
                return self.session.get(url, **kwargs, timeout=5, verify=False)
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.RequestException:
                continue
        raise SejongServerNotAvailableError

    def post(self, url, **kwargs):
        for i in range(self.MAX_RETRIES):
            try:
                return self.session.post(url, **kwargs, timeout=5, verify=False)
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.RequestException:
                continue
        raise SejongServerNotAvailableError

    def login(self, id, password):
        data = {
            "mainLogin": "N",
            "id": id,
            "password": password,
        }

        for i in range(self.MAX_RETRIES):
            try:
                r1 = self.session.post(
                    self.PORTAL_AUTH_URL,
                    headers={
                        **self.DEFAULT_HEADERS,
                        "Referer": "https://portal.sejong.ac.kr",
                        "Host": "portal.sejong.ac.kr",
                    },
                    cookies={"chknos": "false"},
                    data=data,
                    allow_redirects=True,
                    timeout=5.0,
                    verify=False,
                )
                if "ssotoken" in self.session.cookies.get_dict():
                    self.session.get(
                        self.PORTAL_SSO_PROC,
                        headers=self.DEFAULT_HEADERS,
                        allow_redirects=True,
                        timeout=8.0,
                        verify=False,
                    )
                    return
                else:
                    if "result = 'pwdNeedChg'" in r1.text:
                        raise PortalLoginError(
                            401,
                            "일정 횟수 이상 패스워드를 잘못 입력하여 계정이 잠겼습니다. 비밀번호 찾기 페이지에서 비밀번호를 재설정하셔야 합니다.",
                        )
                    elif "result = 'erridpwd'" in r1.text:
                        raise PortalLoginError(
                            401, "아이디나 비밀번호가 일치하지 않습니다."
                        )
                    elif "result = 'invalidDt'" in r1.text:
                        raise PortalLoginError(
                            401,
                            "계정의 사용 허용기간이 종료되었습니다. sj로 시작하는 아이디, 원직번, 성명, 소속부서, 사용사유를 itservice@sejong.ac.kr로 보내주시기 바랍니다. 내용에 따라 사용권한 요청서가 추가로 필요할 수 있습니다.",
                        )
                    elif "result = 'Error'" in r1.text:
                        raise PortalLoginError(
                            401, "아이디나 비밀번호가 일치하지 않습니다."
                        )
                    elif "result = 'invalid'" in r1.text:
                        raise PortalLoginError(
                            401,
                            "이 계정은 계정관리자의 요청으로 현재 로그인이 불가 합니다.",
                        )
                    else:
                        raise PortalLoginError(
                            401, "로그인 처리 중 오류가 발생하였습니다."
                        )
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.RequestException:
                continue
        raise SejongServerNotAvailableError

    def bridge_to_libseat(self):
        # 1) library 인증 세션 확보 (eproxy 흐름 포함)
        self.ensure_library_session()

        # 2) relation/studyroom HTML 받기
        r_rel = self.session.get(
            self.LIBRARY_STUDYROOM_REL,
            headers={
                **self.DEFAULT_HEADERS,
                "Referer": "https://library.sejong.ac.kr/",
            },
            allow_redirects=True,
            timeout=10.0,
            verify=False,
        )

        token_url = self.extract_libseat_token_url(r_rel.text)
        if not token_url:
            return False

        # 3) token URL을 직접 밟아서 libseat 세션 생성
        self.session.get(
            token_url,
            headers={
                **self.DEFAULT_HEADERS,
                "Referer": "https://library.sejong.ac.kr/",
            },
            allow_redirects=True,
            timeout=10.0,
            verify=False,
        )

        # 4) libseat 로그인 확인
        return self.check_libseat_login()

    def bridge_to_library_via_eproxy(self):
        """
        HAR에서 확인된 것처럼 library는 eproxy를 통해 인증되는 흐름이 있음.
        library root(http)부터 밟아서 redirect를 따라가며 세션을 만든다.
        """
        r = self.session.get(
            self.LIBRARY_ROOT_HTTP,
            headers=self.DEFAULT_HEADERS,
            allow_redirects=True,
            timeout=10.0,
            verify=False,
        )
        return r

    def check_libseat_login(self):
        r = self.session.get(
            self.LIBSEAT_CHECKING_URL,
            headers=self.DEFAULT_HEADERS,
            allow_redirects=True,
            timeout=8.0,
            verify=False,
        )

        # 실패 시 XML(등록되지 않은 사용자)로 200을 주는 케이스
        if r.text.lstrip().startswith("<?xml"):
            return False

        m = re.search(r"var\s+userId\s*=\s*['\"]([^'\"]*)['\"]\s*;", r.text)
        user_id = m.group(1) if m else ""
        return bool(user_id)

    def ensure_library_session(self):
        # eproxy/https redirect까지 한번에 밟아서 library 인증 세션을 만든다
        r = self.session.get(
            self.LIBRARY_ROOT_HTTP,
            headers=self.DEFAULT_HEADERS,
            allow_redirects=True,
            timeout=10.0,
            verify=False,
        )
        return r

    def extract_libseat_token_url(self, html: str) -> str | None:
        """
        relation/studyroom 응답 HTML/JS 안에서
        https://libseat.sejong.ac.kr/mobile/MA/LsroomList.php?token=... 형태를 뽑는다.
        """
        # 흔한 패턴 1: window.open("https://libseat...token=...")
        m = re.search(
            r"(https://libseat\.sejong\.ac\.kr/[^\"'\s>]+token=[^\"'\s>]+)", html
        )
        if m:
            return m.group(1)

        # 혹시 상대경로로 박혀있으면 이 패턴도
        m2 = re.search(r"(/mobile/MA/LsroomList\.php\?token=[^\"'\s>]+)", html)
        if m2:
            return "https://libseat.sejong.ac.kr" + m2.group(1)

        return None
