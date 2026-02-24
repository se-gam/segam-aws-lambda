import json

from ..auth.errors import PortalLoginError, SejongServerNotAvailableError
from ..auth.session import SejongPortalSession
from .common import LIBRARY_USER_FIND_URL


def validate_user_availability(id, password, user_name, student_id, year, month, day):
    sessionService = SejongPortalSession(id, password)
    sessionService.library_login()

    r = sessionService.post(
        LIBRARY_USER_FIND_URL,
        data={
            "altPid": student_id,
            "name": user_name,
            "userBlockUser": "Y",
            "year": year,
            "month": month,
            "day": day,
        },
    )

    data = json.loads(r.headers.get("X-JSON").replace("'", '"'))
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

    try:
        status_code, result = validate_user_availability(
            id, password, user_name, student_id, year, month, day
        )
        return {"statusCode": status_code, "body": json.dumps(result, ensure_ascii=False)}
    except (PortalLoginError, SejongServerNotAvailableError) as e:
        return {
            "statusCode": e.status_code,
            "body": json.dumps({"result": e.message}, ensure_ascii=False),
        }
