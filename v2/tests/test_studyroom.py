import json
from unittest.mock import patch, MagicMock

import pytest


# --- Mock HTML Templates ---

STUDYROOM_TABLE_HTML = """
<table class="tb01 width-full">
<tr><th>헤더</th></tr>
<tr><td><a href="javascript:fn('BK001','IP001','RM001')">상세</a></td></tr>
<tr><td><a href="javascript:fn('BK002','IP002','RM002')">상세</a></td></tr>
</table>
"""

STUDYROOM_TABLE_EMPTY_HTML = """
<table class="tb01 width-full">
<tr><th>헤더</th></tr>
</table>
"""

BOOKING_DETAIL_HTML = """
<table class="tb03 width-100">
<tr><th>예약번호</th><td>BK001</td></tr>
<tr><th>방</th><td>RM001</td></tr>
<tr><th>이용시간</th><td>2025-03-01 10:00부터 2시간</td></tr>
<tr><th>동반 사용자</th><td>홍길동:20230001/학부\n김철수:20230002/학부</td></tr>
<tr><th>사용목적</th><td>스터디</td></tr>
</table>
"""

RESERVE_FORM_HTML = """
<form id="frmMain">
<input name="roomId" value="101"/>
<input name="classId" value="0"/>
</form>
"""

CALENDAR_TABLE_HTML = """
<table><tr><th>헤더</th></tr></table>
<table>
<tr><td>1</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>2</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>3</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>4</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>5</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>6</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>7</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>8</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>9</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>10</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>11</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>12</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>13</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>14</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>15</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>16</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>17</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>18</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>19</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>20</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>21</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>22</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>23</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>24</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>25</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>26</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>27</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>28</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>29</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>30</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>31</td><td>9</td><td>10</td><td>11</td></tr>
</table>
"""

CALENDAR_AVAILABLE_TIMES_HTML = """
<th class="td_Deepgray_left">시간</th>
<th class="td_Deepgray_left">9</th>
<th class="td_Deepgray_left">10</th>
<th class="td_Deepgray_left">11</th>
"""

CALENDAR_CLOSED_TABLE_HTML = """
<table><tr><th>헤더</th></tr></table>
<table>
<tr><td>1</td><td>휴관일</td><td>휴관일</td><td>휴관일</td></tr>
<tr><td>2</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>3</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>4</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>5</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>6</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>7</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>8</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>9</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>10</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>11</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>12</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>13</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>14</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>15</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>16</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>17</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>18</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>19</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>20</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>21</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>22</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>23</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>24</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>25</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>26</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>27</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>28</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>29</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>30</td><td>9</td><td>10</td><td>11</td></tr>
<tr><td>31</td><td>9</td><td>10</td><td>11</td></tr>
</table>
"""


def _make_response(text="", headers=None):
    resp = MagicMock()
    resp.text = text
    resp.status_code = 200
    resp.headers = headers or {}
    return resp


# ===== cancel.py tests =====

class TestCancelReservation:
    @patch("v2.studyroom.cancel.SejongPortalSession")
    def test_cancel_success(self, MockSession):
        session = MagicMock()
        MockSession.return_value = session
        session.get.return_value = _make_response(STUDYROOM_TABLE_HTML)
        session.post.return_value = _make_response()

        from v2.studyroom.cancel import cancel_reservation
        code, msg = cancel_reservation("test", "pw", "BK001", "RM001")

        assert code == 200
        assert "취소" in msg
        session.library_login.assert_called_once()

    @patch("v2.studyroom.cancel.SejongPortalSession")
    def test_cancel_not_found(self, MockSession):
        session = MagicMock()
        MockSession.return_value = session
        session.get.return_value = _make_response(STUDYROOM_TABLE_HTML)

        from v2.studyroom.cancel import cancel_reservation
        code, msg = cancel_reservation("test", "pw", "NONEXIST", "RM001")

        assert code == 404
        assert "찾을 수 없" in msg

    @patch("v2.studyroom.cancel.SejongPortalSession")
    def test_cancel_no_reservations(self, MockSession):
        session = MagicMock()
        MockSession.return_value = session
        session.get.return_value = _make_response(STUDYROOM_TABLE_EMPTY_HTML)

        from v2.studyroom.cancel import cancel_reservation
        code, msg = cancel_reservation("test", "pw", "BK001", "RM001")

        assert code == 404  # 테이블에 데이터 행이 없으면 reservations=[] → booking_id not found


# ===== my_reservation.py tests =====

class TestMyReservation:
    @patch("v2.studyroom.my_reservation.SejongPortalSession")
    def test_get_reservations_success(self, MockSession):
        session = MagicMock()
        MockSession.return_value = session
        session.get.return_value = _make_response(STUDYROOM_TABLE_HTML)
        session.post.return_value = _make_response(BOOKING_DETAIL_HTML)

        from v2.studyroom.my_reservation import get_my_reservations
        code, result = get_my_reservations("test", "pw")

        assert code == 200
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "booking_id" in result[0]
        assert "date" in result[0]
        assert "starts_at" in result[0]
        assert "users" in result[0]
        session.library_login.assert_called_once()

    @patch("v2.studyroom.my_reservation.SejongPortalSession")
    def test_get_reservations_empty(self, MockSession):
        session = MagicMock()
        MockSession.return_value = session
        session.get.return_value = _make_response(STUDYROOM_TABLE_EMPTY_HTML)

        from v2.studyroom.my_reservation import get_my_reservations
        code, result = get_my_reservations("test", "pw")

        assert code == 200  # 테이블에 데이터 행이 없으면 reservations=[] → 빈 result 반환
        assert result == []


# ===== reserve.py tests =====

class TestReserve:
    @patch("v2.studyroom.reserve.SejongPortalSession")
    def test_create_reservation_success(self, MockSession):
        session = MagicMock()
        MockSession.return_value = session
        session.get.return_value = _make_response(RESERVE_FORM_HTML)

        post_resp = _make_response(headers={"X-JSON": "{'result':'true'}"})
        session.post.return_value = post_resp

        from v2.studyroom.reserve import create_reservation
        users = [{"student_id": "20230001", "name": "홍길동", "ipid": "IP001"}]
        code, result = create_reservation(
            "test", "pw", "101", users, "2025", "3", "1", "10", "2"
        )

        assert code == 200
        assert "완료" in result["result"]
        session.library_login.assert_called_once()

    @patch("v2.studyroom.reserve.SejongPortalSession")
    def test_create_reservation_fail(self, MockSession):
        session = MagicMock()
        MockSession.return_value = session
        session.get.return_value = _make_response(RESERVE_FORM_HTML)

        post_resp = _make_response(
            text="예약 실패 메시지",
            headers={"X-JSON": "{'result':'false'}"},
        )
        session.post.return_value = post_resp

        from v2.studyroom.reserve import create_reservation
        users = [{"student_id": "20230001", "name": "홍길동", "ipid": "IP001"}]
        code, result = create_reservation(
            "test", "pw", "101", users, "2025", "3", "1", "10", "2"
        )

        assert code == 400
        assert "error" in result


# ===== validate_availability.py tests =====

class TestValidateAvailability:
    @patch("v2.studyroom.validate_availability.SejongPortalSession")
    def test_validate_success(self, MockSession):
        session = MagicMock()
        MockSession.return_value = session

        resp = _make_response(
            headers={"X-JSON": "{'result':'true','ipid':'IP999'}"}
        )
        session.post.return_value = resp

        from v2.studyroom.validate_availability import validate_user_availability
        code, result = validate_user_availability(
            "test", "pw", "홍길동", "20230001", "2025", "3", "1"
        )

        assert code == 200
        assert result["ipid"] == "IP999"
        session.library_login.assert_called_once()

    @patch("v2.studyroom.validate_availability.SejongPortalSession")
    def test_validate_fail(self, MockSession):
        session = MagicMock()
        MockSession.return_value = session

        resp = _make_response(
            headers={"X-JSON": "{'result':'false'}"}
        )
        session.post.return_value = resp

        from v2.studyroom.validate_availability import validate_user_availability
        code, result = validate_user_availability(
            "test", "pw", "홍길동", "20230001", "2025", "3", "1"
        )

        assert code == 400
        assert "error" in result


# ===== calendar.py tests =====

class TestCalendar:
    @patch("v2.studyroom.calendar.datetime")
    @patch("v2.studyroom.calendar.requests.Session")
    def test_get_weekly_calendar_success(self, MockReqSession, mock_dt):
        from datetime import datetime, timedelta

        fake_today = datetime(2025, 3, 5)
        mock_dt.today.return_value = fake_today
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)

        mock_session_instance = MagicMock()
        MockReqSession.return_value = mock_session_instance

        mock_session_instance.post.return_value = _make_response(
            CALENDAR_AVAILABLE_TIMES_HTML + CALENDAR_TABLE_HTML
        )

        from v2.studyroom.calendar import get_weekly_calendar
        result = get_weekly_calendar("101")

        assert result["room_id"] == "101"
        assert isinstance(result["slots"], list)
        assert len(result["slots"]) > 0
        for slot in result["slots"]:
            assert "date" in slot
            assert "time" in slot
            assert "is_reserved" in slot
            assert "is_closed" in slot

    @patch("v2.studyroom.calendar.datetime")
    @patch("v2.studyroom.calendar.requests.Session")
    def test_get_weekly_calendar_closed_day(self, MockReqSession, mock_dt):
        from datetime import datetime, timedelta

        fake_today = datetime(2025, 3, 1)
        mock_dt.today.return_value = fake_today
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)

        mock_session_instance = MagicMock()
        MockReqSession.return_value = mock_session_instance

        mock_session_instance.post.return_value = _make_response(
            CALENDAR_AVAILABLE_TIMES_HTML + CALENDAR_CLOSED_TABLE_HTML
        )

        from v2.studyroom.calendar import get_weekly_calendar
        result = get_weekly_calendar("101")

        assert result["room_id"] == "101"
        # First day should have closed slots
        first_day_slots = [s for s in result["slots"] if s["date"] == "2025-03-01"]
        assert any(s["is_closed"] for s in first_day_slots)


# ===== make_lambda_handler tests =====

class TestMakeLambdaHandler:
    def test_handler_success(self):
        from v2.studyroom.common import make_lambda_handler

        def dummy_func(a, b):
            return 200, f"{a}-{b}"

        handler = make_lambda_handler(dummy_func, ["key_a", "key_b"])
        event = {"body": json.dumps({"key_a": "hello", "key_b": "world"})}
        result = handler(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["result"] == "hello-world"

    def test_handler_optional_param(self):
        from v2.studyroom.common import make_lambda_handler

        def dummy_func(a, b="default"):
            return 200, f"{a}-{b}"

        handler = make_lambda_handler(dummy_func, ["key_a", "key_b?=default"])
        event = {"body": json.dumps({"key_a": "hello"})}
        result = handler(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["result"] == "hello-default"

    def test_handler_portal_login_error(self):
        from v2.studyroom.common import make_lambda_handler
        from v2.auth.errors import PortalLoginError

        def dummy_func(a):
            raise PortalLoginError(401, "로그인 실패")

        handler = make_lambda_handler(dummy_func, ["key_a"])
        event = {"body": json.dumps({"key_a": "test"})}
        result = handler(event, None)

        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert "로그인 실패" in body["result"]
