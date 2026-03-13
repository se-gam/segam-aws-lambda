import re

import bs4 as bs

from ..auth.session import SejongPortalSession
from .common import (
    LIBRARY_STUDYROOM_URL,
    STUDYROOM_BOOKING_CANCEL_RESERCATION_URL,
    STUDYROOM_BOOKING_MY_RESERVATION_URL,
    make_lambda_handler,
)


def _parse_libseat_xml(xml_text: str):
    code_m = re.search(r"<resultCode><!\[CDATA\[(.*?)\]\]></resultCode>", xml_text)
    msg_m = re.search(r"<resultMsg><!\[CDATA\[(.*?)\]\]></resultMsg>", xml_text)
    code = code_m.group(1).strip() if code_m else None
    msg = msg_m.group(1).strip() if msg_m else None
    return code, msg
    

def cancel_reservation(id, password, reserve_no):
    sessionService = SejongPortalSession(id, password)
    sessionService.bridge_to_libseat()

    r = sessionService.get(LIBRARY_STUDYROOM_URL)

    headers = {
        "Referer": STUDYROOM_BOOKING_MY_RESERVATION_URL,
        "Origin": "https://libseat.sejong.ac.kr",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0",
    }

    data = {
        "userID": id,
        "reserveNo": reserve_no,
    }

    r = sessionService.post(
        STUDYROOM_BOOKING_CANCEL_RESERCATION_URL, data=data, headers=headers
    )

    text = r.text or ""
    result_code, result_msg = _parse_libseat_xml(text)

    # result_code가 None이면 비정상 응답(HTML 등)
    if result_code is None:
        return 502, {
            "ok": False,
            "error": "Unexpected response from libseat",
            "raw": text[:5000],
            "status_code": r.status_code,
        }

    ok = result_code == "0"
    return 200, {
        "ok": ok,
        "resultCode": result_code,
        "resultMsg": result_msg,
        "reserveNo": reserve_no,
    }

lambda_handler = make_lambda_handler(
    cancel_reservation,
    ["id", "password", "booking_id", "room_id"],
)
