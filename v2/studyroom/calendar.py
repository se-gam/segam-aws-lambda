import json
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from .common import STUDYROOM_BOOKING_TABLE_URL

def get_weekly_calendar(room_id):
    today = datetime.today()
    end_date = today + timedelta(days=8)
    result = {"room_id": str(room_id), "slots": []}

    session = requests.Session()

    def _fetch_table(year, month):
        r = session.post(
            STUDYROOM_BOOKING_TABLE_URL,
            data={"roomId": room_id, "year": year, "month": month - 1},
            verify=False,
        )
        return r.text

    # 이용 가능 시간대 파싱
    available_time_html = _fetch_table(today.year, today.month)
    available_times = [
        x.text
        for x in BeautifulSoup(available_time_html, "html.parser").find_all(
            "th", {"class": "td_Deepgray_left"}
        )
    ][1:]

    def _parse_table_rows(html):
        """HTML 테이블에서 각 날짜별 슬롯 데이터를 2D 리스트로 파싱"""
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        if len(tables) < 2:
            return []
        rows = tables[1].find_all("tr")
        parsed = []
        for row in rows:
            cells = row.find_all("td")
            if cells:
                parsed.append([cell.text.strip() for cell in cells])
        return parsed

    if today.month == end_date.month:
        html = _fetch_table(today.year, today.month)
        all_rows = _parse_table_rows(html)
        data_rows = all_rows[today.day - 1 : end_date.day]
    else:
        html1 = _fetch_table(today.year, today.month)
        html2 = _fetch_table(end_date.year, end_date.month)
        rows1 = _parse_table_rows(html1)
        rows2 = _parse_table_rows(html2)
        data_rows = rows1[today.day - 1 :] + rows2[: end_date.day]

    for date, row in zip(daterange(today, end_date), data_rows):
        for i, slot in enumerate(row[1:]):
            is_closed = False
            try:
                slot_time = f"{int(slot)}:00"
            except ValueError:
                if slot.strip() == "휴관일":
                    is_closed = True
                slot_time = f"{int(available_times[i])}:00"
            result["slots"].append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "time": slot_time,
                    "is_reserved": slot != available_times[i],
                    "is_closed": is_closed,
                }
            )
    return result


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def lambda_handler(event, context):
    try:
        event = json.loads(event["body"])
        room_id = event["room_id"]
        result = get_weekly_calendar(room_id)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(result, ensure_ascii=False),
        }
    except KeyError:
        return {
            "statusCode": 400,
            "headers": {},
            "body": json.dumps(
                {
                    "message": "Invalid room_id",
                }
            ),
        }
