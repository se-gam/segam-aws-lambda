from __future__ import annotations

import re
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from v2.studyroom.common import STUDYROOM_BOOKING_TABLE_URLS


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


def get_room_names(soup: BeautifulSoup) -> List[str]:
    header = soup.select_one("div.avl-slot")
    if not header:
        return []

    rooms: List[str] = []
    for el in header.select("div.at-title span"):
        room_name = normalize_text(el.get_text())
        if room_name:
            rooms.append(room_name)

    return rooms


def parse_availability(soup: BeautifulSoup) -> Dict[str, List[str]]:
    room_names = get_room_names(soup)
    result: Dict[str, List[str]] = {room: [] for room in room_names}

    rows = soup.select("div.avl-data-slot")

    for row in rows:
        time_el = row.select_one("div.avl-time")
        if not time_el:
            continue

        time_text = normalize_text(time_el.get_text())
        buttons = row.select("div.avl-button")

        for idx, button in enumerate(buttons[:len(room_names)]):
            cell_text = normalize_text(button.get_text())
            has_link = button.select_one("a") is not None

            if has_link or ("예약가능" in cell_text):
                room = room_names[idx]
                result[room].append(time_text)

    return result


def get_date_links(soup: BeautifulSoup, current_url: str) -> List[Tuple[str, str]]:
    links: List[Tuple[str, str]] = []

    for a in soup.select("#dateRow a"):
        href = a.get("href")
        if not href:
            continue

        absolute_url = urljoin(current_url, href)
        reserve_date = extract_reserve_date(absolute_url)

        if reserve_date:
            links.append((reserve_date, absolute_url))

    return links


def crawl_from_url(start_url: str) -> Dict[str, Dict[str, List[str]]]:
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

    results: Dict[str, Dict[str, List[str]]] = {}

    start_soup = fetch_soup(session, start_url)

    start_date = extract_reserve_date(start_url)
    if start_date:
        results[start_date] = parse_availability(start_soup)

    date_links = get_date_links(start_soup, start_url)

    visited_dates = set(results.keys())

    for reserve_date, url in date_links:
        if reserve_date in visited_dates:
            continue

        try:
            soup = fetch_soup(session, url)
            results[reserve_date] = parse_availability(soup)
            visited_dates.add(reserve_date)
        except requests.RequestException:
            pass

    return dict(sorted(results.items(), key=lambda x: x[0]))


def compress_time_ranges(times: List[str]) -> List[str]:
    if not times:
        return []

    def to_minutes(t: str) -> int:
        h, m = map(int, t.split(":"))
        return h * 60 + m

    def to_str(x: int) -> str:
        return f"{x // 60:02d}:{x % 60:02d}"

    minutes = [to_minutes(t) for t in times]
    ranges = []

    start = prev = minutes[0]

    for cur in minutes[1:]:
        if cur == prev + 30:
            prev = cur
        else:
            ranges.append((start, prev))
            start = prev = cur

    ranges.append((start, prev))

    result = []
    for s, e in ranges:
        if s == e:
            result.append(to_str(s))
        else:
            result.append(f"{to_str(s)}~{to_str(e)}")

    return result
