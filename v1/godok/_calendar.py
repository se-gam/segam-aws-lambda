import asyncio
import datetime
import json

from aiohttp import ClientSession
from bs4 import BeautifulSoup

LOGIN_API_ROOT = "http://classic.sejong.ac.kr/userLogin.do"
MONTHLY_CHECK_TABLE_API_ROOT = (
    "http://classic.sejong.ac.kr/schedulePageList.do?menuInfoId=MAIN_02_04"
)


async def get_available_seats(date: str, session):
    payload = {"shDate": date}
    async with session.post(MONTHLY_CHECK_TABLE_API_ROOT, data=payload) as response:
        text = await response.text()

    soup = BeautifulSoup(text, "html.parser")
    table = soup.find_all("tbody")

    tr_elements = table[0].select("tr")

    if (
        tr_elements[0].select_one("td:nth-child(1)").text.strip()
        == "검색된 결과가 없습니다."
    ):
        print(f"{date}에 검색된 결과가 없습니다.")
        return []

    data_for_date = []
    for tr in tr_elements:
        data_id = (
            tr.find("button").get("onclick")[
                tr.find("button").get("onclick").find("(") + 2 : -3
            ]
            if tr.find("button")
            else ""
        )
        time = tr.select_one("td:nth-child(4)").text.strip()
        booked_seats = tr.select_one("td:nth-child(6)").text.strip().split()[0]
        total_seats = tr.select_one("td:nth-child(7)").text.strip().split()[0]

        dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

        iso_string = dt.isoformat()

        data_in_each_time = {
            "data_id": data_id,
            "date_time": iso_string + "+09:00",
            "available_seats": int(total_seats) - int(booked_seats),
            "total_seats": int(total_seats),
        }
        data_for_date.append(data_in_each_time)

    return data_for_date


async def fetch_all_dates(dates, session):
    tasks = [asyncio.create_task(get_available_seats(date, session)) for date in dates]
    seats_by_date = await asyncio.gather(*tasks)
    result = []
    for seats in seats_by_date:
        result.extend(seats)
    return result


async def async_lambda_handler(event, context):
    id = "아이디"
    password = "비밀번호"

    payload = {"userId": id, "password": password, "go": ""}

    async with ClientSession() as session:
        async with session.post(LOGIN_API_ROOT, data=payload) as response:
            if response.history:
                today = datetime.datetime.now()
                dates = [
                    (today + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                    for i in range(1, 32)
                ]

                result = [*(await fetch_all_dates(dates, session))]

                return {
                    "statusCode": 200,
                    "headers": {},
                    "body": json.dumps(result, ensure_ascii=False),
                }
            else:
                return {
                    "statusCode": 400,
                    "headers": {},
                    "body": json.dumps(
                        {
                            "message": "Invalid student_id or password",
                        }
                    ),
                }


def lambda_handler(event, context):
    return asyncio.get_event_loop().run_until_complete(
        async_lambda_handler(event, context)
    )
