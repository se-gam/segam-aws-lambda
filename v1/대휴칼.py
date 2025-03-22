# %%
import json

import bs4 as bs
import requests
import urllib3
from requests import Session
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

s = Session()

headers = {
    "Host": "portal.sejong.ac.kr",
}

cookies = {
    "chknos": "false",
}

headers["Referer"] = "https://portal.sejong.ac.kr"

url1 = "https://portal.sejong.ac.kr/jsp/login/login_action.jsp"

id = "id"
password = "password"

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
    print("로그인 실패")

cookies["ssotoken"] = r1.cookies["ssotoken"]
headers["Cookie"] = f"chknos=false;"

url2 = "http://classic.sejong.ac.kr/_custom/sejong/sso/sso-return.jsp?returnUrl=https://classic.sejong.ac.kr/classic/index.do"
s.get(url2, verify=False)

url3 = "https://classic.sejong.ac.kr/classic/reading/status.do"
r3 = s.get(url3, verify=False)

# %%
with open("test.html", "w") as f:
    f.write(r3.text)


# %%



