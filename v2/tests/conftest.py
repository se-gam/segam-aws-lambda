import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_portal_login():
    """SejongPortalSession의 __init__과 login을 mock하여 실제 포털 호출 방지"""
    with patch("v2.auth.session.SejongPortalSession.__init__", return_value=None) as mock_init, \
         patch("v2.auth.session.SejongPortalSession.login") as mock_login:
        mock_init.return_value = None
        yield mock_init, mock_login


@pytest.fixture
def mock_session_get():
    """SejongPortalSession.get을 mock하여 HTML 응답 반환"""
    with patch("v2.auth.session.SejongPortalSession.get") as mock_get:
        response = MagicMock()
        response.status_code = 200
        response.text = ""
        mock_get.return_value = response
        yield mock_get, response


@pytest.fixture
def mock_session_post():
    """SejongPortalSession.post를 mock하여 HTML/JSON 응답 반환"""
    with patch("v2.auth.session.SejongPortalSession.post") as mock_post:
        response = MagicMock()
        response.status_code = 200
        response.text = ""
        response.headers = {}
        mock_post.return_value = response
        yield mock_post, response
