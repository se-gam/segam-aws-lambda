from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from .common import CN_BOOKING_TABLE_URLS, STUDYROOM_BOOKING_TABLE_URLS, SL_BOOKING_TABLE_URLS

ROOM_TO_URL_INDEX: dict[str, int] = {
    "01": 0,
    "02": 1, "03": 1, "04": 1,
    "05": 2, "06": 2, "07": 2,
    "08": 3, "09": 3, "10": 3,
    "11": 4, "12": 4, "13": 4,
}

SL_TO_URL_INDEX: dict[str, int] = {
  "1": 0, "2": 0, "8": 0,
  "9": 1, "10": 1, "11": 1,
  "12": 2, "13": 2, "14": 2,
  "3": 3, "4": 3, "5": 3,
  "6": 4, "15": 4, "16": 4,
  "17": 5, "18": 5, "19": 5
}

CN_TO_URL_INDEX: dict[str, int] = {
  "01": 0, "02": 0, "03": 0,
  "04": 1, "05": 1, "06": 1,
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_reserve_date(url: str) -> str | None:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    values = qs.get("reserveDate")
    return values[0] if values else None


def fetch_soup(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url, timeout=15)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    return BeautifulSoup(response.text, "html.parser")


def get_room_names(soup: BeautifulSoup) -> list[str]:
    header = soup.select_one("div.avl-slot")
    if not header:
        return []

    rooms: list[str] = []
    for el in header.select("div.at-title span"):
        room_name = normalize_text(el.get_text())
        if room_name:
            rooms.append(room_name)

    return rooms


def parse_all_slots(soup: BeautifulSoup) -> dict[str, dict[str, bool]]:
    room_names = get_room_names(soup)
    result: dict[str, dict[str, bool]] = {room: {} for room in room_names}

    rows = soup.select("div.avl-data-slot")

    for row in rows:
        time_el = row.select_one("div.avl-time")
        if not time_el:
            continue

        time_text = normalize_text(time_el.get_text())
        buttons = row.select("div.avl-button")

        for idx, button in enumerate(buttons[: len(room_names)]):
            if idx >= len(room_names):
                break

            room = room_names[idx]
            cell_text = normalize_text(button.get_text())
            has_link = button.select_one("a") is not None

            is_reserved = not (has_link or "예약가능" in cell_text)
            result[room][time_text] = is_reserved

    return result


def get_date_links(soup: BeautifulSoup, current_url: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []

    for a in soup.select("#dateRow a"):
        href = a.get("href")
        if not href:
            continue

        absolute_url = urljoin(current_url, href)
        reserve_date = extract_reserve_date(absolute_url)

        if reserve_date:
            links.append((reserve_date, absolute_url))

    return links


def crawl_calendar_from_url(
    start_url: str,
) -> dict[str, dict[str, dict[str, bool]]]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
    )

    results: dict[str, dict[str, dict[str, bool]]] = {}

    start_soup = fetch_soup(session, start_url)

    start_date = extract_reserve_date(start_url)
    if start_date:
        results[start_date] = parse_all_slots(start_soup)

    date_links = get_date_links(start_soup, start_url)

    visited_dates = set(results.keys())

    for reserve_date, url in date_links:
        if reserve_date in visited_dates:
            continue

        try:
            soup = fetch_soup(session, url)
            results[reserve_date] = parse_all_slots(soup)
            visited_dates.add(reserve_date)
        except requests.RequestException:
            pass
    return dict(sorted(results.items(), key=lambda x: x[0]))


def format_date(date_str: str) -> str:
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return date_str


def get_weekly_calendar(room_type, room_id: str) -> dict[str, str | list[dict[str, str | bool]]]:
    slots: list[dict[str, str | bool]] = []
    result = {"room_name": room_type+" "+room_id, "slots": slots}

    all_data: dict[str, dict[str, bool]] = {}
    all_time_slots: set[str] = set()

    url = ""
    room_name = ""
    if room_type == "스터디룸":
      normalized_room_id = room_id.zfill(2)
      url_index = ROOM_TO_URL_INDEX.get(normalized_room_id)
      if url_index is None:
          return result
      url = STUDYROOM_BOOKING_TABLE_URLS[url_index]
      room_name = f"{normalized_room_id}스터디룸"
    elif room_type == "SL":
      url_index = SL_TO_URL_INDEX.get(room_id)
      if url_index is None:
          return result
      url = SL_BOOKING_TABLE_URLS[url_index]
      room_name = f"SL{room_id}"
    elif room_type == "시네마룸":
      normalized_room_id = room_id.zfill(2)
      url_index = CN_TO_URL_INDEX.get(normalized_room_id)
      if url_index is None:
          return result
      url = CN_BOOKING_TABLE_URLS[url_index]
      room_name = f"시네마룸{room_id}-3인실"

    try:
        crawled = crawl_calendar_from_url(url)

        for date_str, rooms in crawled.items():
            if room_name in rooms:
                formatted_date = format_date(date_str)
                if formatted_date not in all_data:
                    all_data[formatted_date] = {}
                all_data[formatted_date].update(rooms[room_name])
                all_time_slots.update(rooms[room_name].keys())
    except requests.RequestException:
        pass

    today = datetime.today()
    end_date = today + timedelta(days=8)

    sorted_time_slots = sorted(all_time_slots)

    for single_date in daterange(today, end_date):
        date_str = single_date.strftime("%Y-%m-%d")

        if date_str in all_data:
            time_slots = all_data[date_str]
            for time_slot in sorted(time_slots.keys()):
                is_reserved = time_slots[time_slot]
                slots.append(
                    {
                        "date": date_str,
                        "time": time_slot,
                        "is_reserved": is_reserved,
                        "is_closed": False,
                    }
                )
        else:
            for time_slot in sorted_time_slots:
                slots.append(
                    {
                        "date": date_str,
                        "time": time_slot,
                        "is_reserved": False,
                        "is_closed": True,
                    }
                )

    return result


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        room_type, room_no = body["room_name"].split()
        result = get_weekly_calendar(room_type, room_no)

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
                    "message": "Invalid room_name",
                }
            ),
        }
