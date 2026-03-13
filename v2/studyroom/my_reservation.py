import re
from time import sleep

import bs4 as bs

from ..auth.session import SejongPortalSession
from .common import (
    STUDYROOM_BOOKING_MY_RESERVATION_URL,
    make_lambda_handler,
)

RESERVE_NO_RE = re.compile(r"'(\d{10,})'")  # reserveNo는 숫자 긴 거(대충 10자리 이상)


def extract_reserve_no_from_status(it) -> str | None:
    status_el = it.select_one(".status")
    if not status_el:
        return None

    onclick = status_el.get("onclick", "") or ""

    m = RESERVE_NO_RE.search(onclick)
    if m:
        return m.group(1)

    m2 = re.search(r"\b(\d{10,})\b", onclick)
    return m2.group(1) if m2 else None


def parse_time_range(time_str: str) -> tuple[str | None, str | None]:
    if not time_str or "~" not in time_str:
        return None, None
    
    parts = time_str.split("~")
    start = parts[0].strip()
    end = parts[1].strip()
    
    try:
        start_hour, start_min = map(int, start.split(":"))
        end_hour, end_min = map(int, end.split(":"))
        
        duration_hours = end_hour - start_hour
        duration_mins = end_min - start_min
        
        if duration_mins < 0:
            duration_hours -= 1
            duration_mins += 60
        
        if duration_mins == 0:
            duration = f"{duration_hours}"
        else:
            duration = f"{duration_hours}"
        
        return start, duration
    except (ValueError, IndexError):
        return None, None


def get_my_reservations(id, password):
    sessionService = SejongPortalSession(id, password)
    sleep(0.5)

    if not sessionService.bridge_to_libseat():
        return 500, {"message": "libseat bridge failed"}

    r = sessionService.get(STUDYROOM_BOOKING_MY_RESERVATION_URL)
    soup = bs.BeautifulSoup(r.text, "html.parser")

    tabs = soup.select(".tab-content")
    if len(tabs) < 2:
        return 200, []
    
    results = []
    for study_tab in [tabs[1], tabs[2], tabs[3]]:
        items = study_tab.select(".item")
    
        for it in items:
            date = (
                it.select_one(".date").get_text(strip=True)
                if it.select_one(".date")
                else ""
            )
            time = (
                it.select_one(".time").get_text(strip=True)
                if it.select_one(".time")
                else ""
            )
            room = (
                it.select_one(".room").get_text(strip=True)
                if it.select_one(".room")
                else ""
            )
    
            reserve_no = extract_reserve_no_from_status(it)
            starts_at, duration = parse_time_range(time)
    
            results.append(
                {
                    "booking_id": reserve_no,
                    "ipid": None,
                    "room_name": room,
                    "duration": duration,
                    "date": date,
                    "starts_at": starts_at,
                }
            )

    return 200, results


lambda_handler = make_lambda_handler(
    get_my_reservations,
    ["student_id", "password"],
)
