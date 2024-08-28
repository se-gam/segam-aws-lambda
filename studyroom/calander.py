import io
import json
from datetime import datetime, timedelta

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_weekly_calendar(room_id):
    url = "https://library.sejong.ac.kr/studyroom/BookingTable.axa"
    today = datetime.today()
    end_date = today + timedelta(days=8)
    result = {"room_id": str(room_id), "slots": []}

    available_time_url = "https://library.sejong.ac.kr/studyroom/BookingTable.axa"

    available_time_res = requests.post(
        available_time_url,
        data={"roomId": room_id, "year": today.year, "month": today.month - 1},
        verify=False,
    )

    available_times = [
        x.text
        for x in BeautifulSoup(available_time_res.text, "html.parser").find_all(
            "th", {"class": "td_Deepgray_left"}
        )
    ][1:]

    if today.month == end_date.month:
        r = requests.post(
            url,
            data={"roomId": room_id, "year": today.year, "month": today.month - 1},
            verify=False,
        )

        data = pd.read_html(io.StringIO(r.text))[1][today.day - 1 : end_date.day]
    else:
        r1 = requests.post(
            url,
            data={"roomId": room_id, "year": today.year, "month": today.month - 1},
            verify=False,
        )
        r2 = requests.post(
            url,
            data={
                "roomId": room_id,
                "year": end_date.year,
                "month": end_date.month - 1,
            },
            verify=False,
        )

        data = pd.concat(
            [
                pd.read_html(io.StringIO(r1.text))[1][today.day - 1 :],
                pd.read_html(io.StringIO(r2.text))[1][: end_date.day],
            ],
            axis=0,
        )

    for date, (_, day) in zip(daterange(today, end_date), data.iterrows()):
        for i, slot in enumerate(day.values[1:]):
            is_closed = False
            try:
                slot_time = f"{int(slot)}:00"
            except:
                if slot.strip() == "휴관일":
                    is_closed = True
                else:
                    is_closed = False
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
