import json
from dataclasses import dataclass
from enum import Enum

from ..auth.errors import PortalLoginError, SejongServerNotAvailableError

LIBRARY_STUDYROOM_URL = "https://library.sejong.ac.kr/studyroom/Main.ax"
STUDYROOM_BOOKING_PROCESS_URL = (
    "https://libseat.sejong.ac.kr/mobile/MA/sroomReserve.php"
)
LIBRARY_USER_FIND_URL = "https://library.sejong.ac.kr/studyroom/UserFind.axa"

STUDYROOM_BOOKING_TABLE_URLS = [
    "https://libseat.sejong.ac.kr/mobile/MA/sroomMap.php?roomGB=S1&seatCnt=12&sroomTitle=%EA%B7%B8%EB%A3%B9%EC%8A%A4%ED%84%B0%EB%94%94%EB%A3%B812%EC%9D%B8",
    "https://libseat.sejong.ac.kr/mobile/MA/sroomMap.php?roomGB=S1&seatCnt=6&seq=0&sroomTitle=%EA%B7%B8%EB%A3%B9%EC%8A%A4%ED%84%B0%EB%94%94%EB%A3%B86%EC%9D%B8%EC%8B%A4",
    "https://libseat.sejong.ac.kr/mobile/MA/sroomMap.php?roomGB=S1&seatCnt=6&seq=1&sroomTitle=%EA%B7%B8%EB%A3%B9%EC%8A%A4%ED%84%B0%EB%94%94%EB%A3%B86%EC%9D%B8%EC%8B%A4",
    "https://libseat.sejong.ac.kr/mobile/MA/sroomMap.php?roomGB=S1&seatCnt=6&seq=2&sroomTitle=%EA%B7%B8%EB%A3%B9%EC%8A%A4%ED%84%B0%EB%94%94%EB%A3%B86%EC%9D%B8%EC%8B%A4",
    "https://libseat.sejong.ac.kr/mobile/MA/sroomMap.php?roomGB=S1&seatCnt=6&seq=3&sroomTitle=%EA%B7%B8%EB%A3%B9%EC%8A%A4%ED%84%B0%EB%94%94%EB%A3%B86%EC%9D%B8%EC%8B%A4",
]

SL_BOOKING_TABLE_URLS = [
    "https://libseat.sejong.ac.kr/mobile/MA/loungeMap.php?roomGB=S3&seatCnt=6&seq=0&sroomTitle=S-Lounge%206%EC%9D%B8%EC%84%9D",
    "https://libseat.sejong.ac.kr/mobile/MA/loungeMap.php?roomGB=S3&seatCnt=6&seq=1&sroomTitle=S-Lounge%206%EC%9D%B8%EC%84%9D",
    "https://libseat.sejong.ac.kr/mobile/MA/loungeMap.php?roomGB=S3&seatCnt=6&seq=2&sroomTitle=S-Lounge%206%EC%9D%B8%EC%84%9D",
    "https://libseat.sejong.ac.kr/mobile/MA/loungeMap.php?roomGB=S3&seatCnt=4&seq=0&sroomTitle=S-Loung%204%EC%9D%B8%EC%84%9D",
    "https://libseat.sejong.ac.kr/mobile/MA/loungeMap.php?roomGB=S3&seatCnt=4&seq=1&sroomTitle=S-Loung%204%EC%9D%B8%EC%84%9D",
    "https://libseat.sejong.ac.kr/mobile/MA/loungeMap.php?roomGB=S3&seatCnt=4&seq=2&sroomTitle=S-Loung%204%EC%9D%B8%EC%84%9D",
]

CN_BOOKING_TABLE_URLS = [
    "https://libseat.sejong.ac.kr/mobile/MA/cinemaMap.php?roomGB=S2&seatCnt=3&seq=0&sroomTitle=%EC%8B%9C%EB%84%A4%EB%A7%88%EB%A3%B8%203%EC%9D%B8%EC%8B%A4",
    "https://libseat.sejong.ac.kr/mobile/MA/cinemaMap.php?roomGB=S2&seatCnt=3&seq=1&sroomTitle=%EC%8B%9C%EB%84%A4%EB%A7%88%EB%A3%B8%203%EC%9D%B8%EC%8B%A4",
]

STUDYROOM_BOOKING_MY_RESERVATION_URL = (
    "https://libseat.sejong.ac.kr/mobile/MA/mySeat.php"
)
STUDYROOM_BOOKING_CANCEL_RESERCATION_URL = (
    "https://libseat.sejong.ac.kr/mobile/MA/cancelSroom.php"
)


class RoomGB(Enum):
    STUDY_ROOM = "S1"
    SL = "S3"


@dataclass(frozen=True)
class StudyRoomInfo:
    """스터디룸 메타데이터(방 -> 파라미터 종속 관계)."""

    seat_cnt: int  # 6 or 12
    sroom_no: int  # URL의 sroomNo
    sroom_name: str  # URL의 sroomName (예: "08스터디룸")

    @property
    def sroom_title(self) -> str:
        if self.seat_cnt == 12:
            return "그룹스터디룸12인"
        if self.seat_cnt == 6:
            return "그룹스터디룸6인실"
        return f"그룹스터디룸{self.seat_cnt}인"


class StudyRoom(Enum):
    ROOM_01 = StudyRoomInfo(seat_cnt=12, sroom_no=1, sroom_name="01스터디룸")

    ROOM_02 = StudyRoomInfo(seat_cnt=6, sroom_no=2, sroom_name="02스터디룸")
    ROOM_03 = StudyRoomInfo(seat_cnt=6, sroom_no=3, sroom_name="03스터디룸")
    ROOM_04 = StudyRoomInfo(seat_cnt=6, sroom_no=4, sroom_name="04스터디룸")

    ROOM_05 = StudyRoomInfo(seat_cnt=6, sroom_no=5, sroom_name="05스터디룸")
    ROOM_06 = StudyRoomInfo(seat_cnt=6, sroom_no=6, sroom_name="06스터디룸")
    ROOM_07 = StudyRoomInfo(seat_cnt=6, sroom_no=7, sroom_name="07스터디룸")

    ROOM_08 = StudyRoomInfo(seat_cnt=6, sroom_no=8, sroom_name="08스터디룸")
    ROOM_09 = StudyRoomInfo(seat_cnt=6, sroom_no=9, sroom_name="09스터디룸")
    ROOM_10 = StudyRoomInfo(seat_cnt=6, sroom_no=10, sroom_name="10스터디룸")

    ROOM_11 = StudyRoomInfo(seat_cnt=6, sroom_no=11, sroom_name="11스터디룸")
    ROOM_12 = StudyRoomInfo(seat_cnt=6, sroom_no=12, sroom_name="12스터디룸")
    ROOM_13 = StudyRoomInfo(seat_cnt=6, sroom_no=13, sroom_name="13스터디룸")

    SL1 = StudyRoomInfo(seat_cnt=6, sroom_no=19, sroom_name="SL1")
    SL2 = StudyRoomInfo(seat_cnt=6, sroom_no=20, sroom_name="SL2")
    SL8 = StudyRoomInfo(seat_cnt=6, sroom_no=26, sroom_name="SL8")

    SL9 = StudyRoomInfo(seat_cnt=6, sroom_no=27, sroom_name="SL9")
    SL10 = StudyRoomInfo(seat_cnt=6, sroom_no=28, sroom_name="SL10")
    SL11 = StudyRoomInfo(seat_cnt=6, sroom_no=29, sroom_name="SL11")

    SL12 = StudyRoomInfo(seat_cnt=6, sroom_no=30, sroom_name="SL12")
    SL13 = StudyRoomInfo(seat_cnt=6, sroom_no=31, sroom_name="SL13")
    SL14 = StudyRoomInfo(seat_cnt=6, sroom_no=32, sroom_name="SL14")
    
    SL3 = StudyRoomInfo(seat_cnt=4, sroom_no=21, sroom_name="SL3")
    SL4 = StudyRoomInfo(seat_cnt=4, sroom_no=22, sroom_name="SL4")
    SL5 = StudyRoomInfo(seat_cnt=4, sroom_no=23, sroom_name="SL5")

    SL6 = StudyRoomInfo(seat_cnt=4, sroom_no=24, sroom_name="SL6")
    SL15 = StudyRoomInfo(seat_cnt=4, sroom_no=33, sroom_name="SL15")
    SL16 = StudyRoomInfo(seat_cnt=4, sroom_no=34, sroom_name="SL16")

    SL17 = StudyRoomInfo(seat_cnt=4, sroom_no=35, sroom_name="SL17")
    SL18 = StudyRoomInfo(seat_cnt=4, sroom_no=36, sroom_name="SL18")
    SL19 = StudyRoomInfo(seat_cnt=4, sroom_no=37, sroom_name="SL19")

    CN1 = StudyRoomInfo(seat_cnt=3, sroom_no=14, sroom_name="시네마룸01-3인실")
    CN2 = StudyRoomInfo(seat_cnt=3, sroom_no=15, sroom_name="시네마룸02-3인실")
    CN3 = StudyRoomInfo(seat_cnt=3, sroom_no=16, sroom_name="시네마룸03-3인실")

    CN4 = StudyRoomInfo(seat_cnt=3, sroom_no=17, sroom_name="시네마룸04-3인실")
    CN5 = StudyRoomInfo(seat_cnt=3, sroom_no=18, sroom_name="시네마룸05-3인실")
    CN6 = StudyRoomInfo(seat_cnt=3, sroom_no=38, sroom_name="시네마룸06-3인실")

    @property
    def info(self) -> StudyRoomInfo:
        return self.value


def make_lambda_handler(func, body_keys):
    """공통 lambda_handler 래퍼.

    Args:
        func: 비즈니스 로직 함수 (status_code, result) 튜플 반환
        body_keys: event["body"]에서 추출할 키 리스트.
                   "key" → 필수, "key?" → 선택(기본값 None), "key?=default" → 선택(기본값 지정)
    """

    def handler(event, context):
        body = json.loads(event["body"])
        args = []
        for key in body_keys:
            if "?=" in key:
                name, default = key.split("?=", 1)
                args.append(body.get(name, default))
            elif key.endswith("?"):
                args.append(body.get(key[:-1]))
            else:
                args.append(body[key])

        try:
            status_code, result = func(*args)
            return {
                "statusCode": status_code,
                "body": json.dumps({"result": result}, ensure_ascii=False),
            }
        except (PortalLoginError, SejongServerNotAvailableError) as e:
            return {
                "statusCode": e.status_code,
                "body": json.dumps({"result": e.message}, ensure_ascii=False),
            }

    return handler
