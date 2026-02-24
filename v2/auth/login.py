import json

from bs4 import BeautifulSoup

from .errors import PortalLoginError, SejongServerNotAvailableError
from .session import SejongPortalSession


def get_user_info(student_id, password):
    sessionService = SejongPortalSession(student_id, password)

    r = sessionService.get("https://portal.sejong.ac.kr/user/index.do")
    soup = BeautifulSoup(r.text, "html.parser")

    info = {}
    info_area = soup.find("div", {"class": "uInfoBox"})
    if info_area:
        spans = info_area.find_all("span")
        if spans:
            info["name"] = spans[0].text.strip()
        dds = info_area.find_all("dd")
        for dd in dds:
            text = dd.text.strip()
            if "학부" in text or "학과" in text or "대학" in text:
                info["department"] = text
            elif text.isdigit() and len(text) <= 1:
                info["grade"] = int(text)

    return 200, {
        "name": info.get("name", ""),
        "department": info.get("department", ""),
        "grade": info.get("grade", 1),
        "studentId": student_id,
        "year": int(student_id[:2]),
    }


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        student_id = body["id"]
        password = body["password"]

        status_code, result = get_user_info(student_id, password)
        return {
            "statusCode": status_code,
            "headers": {},
            "body": json.dumps(result, ensure_ascii=False),
        }
    except (PortalLoginError, SejongServerNotAvailableError) as e:
        return {
            "statusCode": e.status_code,
            "body": json.dumps({"result": e.message}, ensure_ascii=False),
        }
    except KeyError:
        return {
            "statusCode": 400,
            "headers": {},
            "body": json.dumps(
                {
                    "message": "Invalid student_id or password",
                }
            ),
        }
