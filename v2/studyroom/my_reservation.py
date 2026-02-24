import bs4 as bs

from ..auth.session import SejongPortalSession
from ..auth.session import SejongPortalSession
from .common import LIBRARY_STUDYROOM_URL, STUDYROOM_BOOKING_DETAIL_URL, make_lambda_handler


def get_my_reservations(id, password):
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
            booking_id = x.find("a").get("href").split("'")[1]
            ipid = x.find("a").get("href").split("'")[3]
            room_id = x.find("a").get("href").split("'")[5]

            reservations.append(
                {
                    "booking_id": booking_id,
                    "ipid": ipid,
                    "room_id": room_id,
                }
            )
    except AttributeError:
        return 404, "예약 내역이 없습니다."
    
    result = []

    for reservation in reservations:
        r4 = sessionService.post(
            STUDYROOM_BOOKING_DETAIL_URL,
            data={
                "bookingId": reservation["booking_id"],
                "ipid": reservation["ipid"],
                "roomId": reservation["room_id"],
            },
        )

        tmp = {
            "booking_id": reservation["booking_id"],
            "ipid": reservation["ipid"],
            "room_id": reservation["room_id"],
        }

        for x in (
            bs.BeautifulSoup(r4.text, "html.parser")
            .find_all("table", {"class": "tb03 width-100"})[0]
            .find_all("tr")[2:]
        ):
            if x.find("th").text.strip() == "이용시간":
                tmp["duration"] = x.find("td").text.strip().split("부터")[1]
                _date, _time = (
                    x.find("td").text.strip().split("부터")[0].strip().split(" ")
                )
                tmp["date"] = _date
                tmp["starts_at"] = _time
            elif x.find("th").text.strip() == "동반 사용자":
                raw_users = [
                    _.strip().split(":") for _ in x.find("td").text.strip().split("\n")
                ]
                users = []
                for user in raw_users:
                    users.append(
                        {
                            "name": user[0].strip(),
                            "student_id": user[1].split("/")[0].strip(),
                        }
                    )
                tmp["users"] = users
            elif x.find("th").text.strip() == "사용목적":
                tmp["purpose"] = x.find("td").text.strip()

        if tmp not in result:
            result.append(tmp)

    return 200, result


lambda_handler = make_lambda_handler(
    get_my_reservations,
    ["student_id", "password"],
)
