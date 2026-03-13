import json

from ..auth.session import SejongPortalSession
from .common import STUDYROOM_BOOKING_PROCESS_URL


def create_reservation(
    id,
    password,
    room_id: int,
    users,
    year,
    month,
    day,
    start_time,
    hours,
    purpose="공부",
):
    sessionService = SejongPortalSession(id, password)

    if not sessionService.bridge_to_libseat():
        raise Exception("libseat login failed")

    user_ids = "|".join(u["student_id"] for u in users)
    user_names = "|".join(u["name"] for u in users)

    p2 = {
        "userID": user_ids,
        "userName": user_names,
        "roomNo": room_id,
        "reserveDate": year + month + day,
        "startTime": start_time,
        "useTime": str(60 * hours),
    }

    r2 = sessionService.post(
        STUDYROOM_BOOKING_PROCESS_URL,
        data=p2,
    )

    if "<resultCode><![CDATA[0]]>" not in r2.text:
        raise Exception("Reservation failed")

    return 200, {"result": "예약이 완료되었습니다."}

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
    except Exception as e:
        return {"statusCode": 400, "body": json.dumps({"error": str(e)}, ensure_ascii=False)}

