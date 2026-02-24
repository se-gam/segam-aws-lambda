import json

import bs4 as bs

from ..auth.errors import PortalLoginError, SejongServerNotAvailableError
from ..auth.session import SejongPortalSession
from .common import STUDYROOM_RESERVE_URL, STUDYROOM_BOOKING_PROCESS_URL


def create_reservation(
    id, password, room_id, users, year, month, day, start_time, hours, purpose="공부"
):
    sessionService = SejongPortalSession(id, password)
    sessionService.library_login()

    r = sessionService.get(STUDYROOM_RESERVE_URL + str(room_id))

    soup = bs.BeautifulSoup(r.text, "html.parser")

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

    r2 = sessionService.post(
        STUDYROOM_BOOKING_PROCESS_URL,
        data=data,
    )

    if "true" in r2.headers.get("X-JSON"):
        return 200, {"result": "예약이 완료되었습니다."}
    else:
        return 400, {"error": r2.text.strip()}


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

    try:
        status_code, result = create_reservation(
            id, password, room_id, users, year, month, day, start_time, hours, purpose
        )
        return {"statusCode": status_code, "body": json.dumps(result, ensure_ascii=False)}

    except (PortalLoginError, SejongServerNotAvailableError) as e:
        return {
            "statusCode": e.status_code,
            "body": json.dumps({"result": e.message}, ensure_ascii=False),
        }
