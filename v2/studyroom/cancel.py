import bs4 as bs

from ..auth.session import SejongPortalSession
from ..auth.session import SejongPortalSession
from .common import LIBRARY_STUDYROOM_URL, make_lambda_handler


def cancel_reservation(id, password, booking_id, room_id, cancel_msg="잘못 예약"):
    sessionService = SejongPortalSession(id, password)
    sessionService.library_login()

    r = sessionService.get(LIBRARY_STUDYROOM_URL)

    reservations = []

    try:
        for x in (
            bs.BeautifulSoup(r.text, "html.parser")
            .find_all("table", {"class": "tb01 width-full"})[-1]
            .find_all("tr")[1:]
        ):
            _booking_id = x.find("a").get("href").split("'")[1]
            ipid = x.find("a").get("href").split("'")[3]
            room_id = x.find("a").get("href").split("'")[5]

            reservations.append(
                {
                    "booking_id": _booking_id,
                    "ipid": ipid,
                    "room_id": room_id,
                }
            )
    except AttributeError:
        return 400, "현재 스터디룸 예약 내역이 없습니다."

    if booking_id not in [x["booking_id"] for x in reservations]:
        return 404, "예약을 찾을 수 없습니다."

    sessionService.post(
        "https://library.sejong.ac.kr/studyroom/BookingProcess.axa",
        data={
            "cancelMsg": cancel_msg,
            "bookingId": booking_id,
            "expired": "C",
            "roomId": room_id,
            "mode": "update",
            "classId": "0",
        },
    )

    return 200, "예약이 취소되었습니다."


lambda_handler = make_lambda_handler(
    cancel_reservation,
    ["id", "password", "booking_id", "room_id", "cancel_msg?=잘못 예약"],
)
