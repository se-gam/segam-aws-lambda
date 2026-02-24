import json
import pytest
from unittest.mock import patch, MagicMock, call
from requests.exceptions import Timeout, RequestException

from v2.auth.session import SejongPortalSession
from v2.auth.login import get_user_info, lambda_handler
from v2.auth.errors import PortalLoginError, SejongServerNotAvailableError


class TestSejongPortalSessionLogin:
    """Test SejongPortalSession.login method"""

    def test_login_success_with_ssotoken(self):
        """Test successful login when ssotoken is in cookies"""
        with patch("v2.auth.session.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock successful response with ssotoken
            mock_response = MagicMock()
            mock_response.cookies = {"ssotoken": "test_token_value"}
            mock_response.text = ""
            mock_session.post.return_value = mock_response
            
            # Should not raise any exception
            session = SejongPortalSession("test_id", "test_password")
            
            # Verify post was called with correct parameters
            mock_session.post.assert_called()
            call_args = mock_session.post.call_args
            assert call_args[0][0] == "https://portal.sejong.ac.kr/jsp/login/login_action.jsp"
            assert call_args[1]["data"]["id"] == "test_id"
            assert call_args[1]["data"]["password"] == "test_password"

    def test_login_error_erridpwd(self):
        """Test login failure with erridpwd error code"""
        with patch("v2.auth.session.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock response with erridpwd error
            mock_response = MagicMock()
            mock_response.cookies = {}
            mock_response.text = "result = 'erridpwd'"
            mock_session.post.return_value = mock_response
            
            # Should raise PortalLoginError
            with pytest.raises(PortalLoginError) as exc_info:
                SejongPortalSession("test_id", "wrong_password")
            
            assert exc_info.value.status_code == 401
            assert "아이디나 비밀번호가 일치하지 않습니다" in exc_info.value.message

    def test_login_error_pwdneedchg(self):
        """Test login failure with pwdNeedChg error code"""
        with patch("v2.auth.session.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock response with pwdNeedChg error
            mock_response = MagicMock()
            mock_response.cookies = {}
            mock_response.text = "result = 'pwdNeedChg'"
            mock_session.post.return_value = mock_response
            
            # Should raise PortalLoginError
            with pytest.raises(PortalLoginError) as exc_info:
                SejongPortalSession("test_id", "test_password")
            
            assert exc_info.value.status_code == 401
            assert "계정이 잠겼습니다" in exc_info.value.message

    def test_login_server_unavailable_timeout(self):
        """Test login failure when server times out after max retries"""
        with patch("v2.auth.session.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock timeout exception
            mock_session.post.side_effect = Timeout("Connection timeout")
            
            # Should raise SejongServerNotAvailableError
            with pytest.raises(SejongServerNotAvailableError) as exc_info:
                SejongPortalSession("test_id", "test_password")
            
            assert exc_info.value.status_code == 503
            assert "세종대학교 서버가 응답이 없습니다" in exc_info.value.message
            # Verify retries happened (MAX_RETRIES = 3)
            assert mock_session.post.call_count == 3

    def test_login_error_invaliddt(self):
        """Test login failure with invalidDt error code"""
        with patch("v2.auth.session.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock response with invalidDt error
            mock_response = MagicMock()
            mock_response.cookies = {}
            mock_response.text = "result = 'invalidDt'"
            mock_session.post.return_value = mock_response
            
            # Should raise PortalLoginError
            with pytest.raises(PortalLoginError) as exc_info:
                SejongPortalSession("test_id", "test_password")
            
            assert exc_info.value.status_code == 401
            assert "사용 허용기간이 종료되었습니다" in exc_info.value.message

    def test_login_error_invalid(self):
        """Test login failure with invalid error code"""
        with patch("v2.auth.session.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock response with invalid error
            mock_response = MagicMock()
            mock_response.cookies = {}
            mock_response.text = "result = 'invalid'"
            mock_session.post.return_value = mock_response
            
            # Should raise PortalLoginError
            with pytest.raises(PortalLoginError) as exc_info:
                SejongPortalSession("test_id", "test_password")
            
            assert exc_info.value.status_code == 401
            assert "로그인이 불가" in exc_info.value.message


class TestSejongPortalSessionLibraryLogin:
    """Test SejongPortalSession.library_login method"""

    def test_library_login_calls_get_with_correct_url(self):
        """Test that library_login calls get with the correct SSO URL"""
        with patch("v2.auth.session.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock successful login
            mock_response = MagicMock()
            mock_response.cookies = {"ssotoken": "test_token"}
            mock_response.text = ""
            mock_session.post.return_value = mock_response
            
            # Create session instance
            session = SejongPortalSession("test_id", "test_password")
            
            # Mock the get method
            with patch.object(session, "get") as mock_get:
                mock_get.return_value = MagicMock()
                
                # Call library_login
                session.library_login()
                
                # Verify get was called with the correct URL
                mock_get.assert_called_once_with("http://library.sejong.ac.kr/sso/Login.ax")

    def test_library_login_handles_timeout(self):
        """Test that library_login propagates timeout errors"""
        with patch("v2.auth.session.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock successful login
            mock_response = MagicMock()
            mock_response.cookies = {"ssotoken": "test_token"}
            mock_response.text = ""
            mock_session.post.return_value = mock_response
            
            # Create session instance
            session = SejongPortalSession("test_id", "test_password")
            
            # Mock the get method to raise timeout
            with patch.object(session, "get") as mock_get:
                mock_get.side_effect = SejongServerNotAvailableError()
                
                # Should raise SejongServerNotAvailableError
                with pytest.raises(SejongServerNotAvailableError):
                    session.library_login()


class TestLoginLambdaHandler:
    """Test lambda_handler function in login.py"""

    def test_lambda_handler_success(self):
        """Test successful login through lambda_handler"""
        with patch("v2.auth.login.SejongPortalSession") as mock_session_class:
            # Mock session instance
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock portal page response with user info
            mock_response = MagicMock()
            mock_response.text = """
            <html>
                <div class="uInfoBox">
                    <span>홍길동</span>
                    <dd>컴퓨터공학부</dd>
                    <dd>3</dd>
                </div>
            </html>
            """
            mock_session.get.return_value = mock_response
            
            # Create event
            event = {
                "body": json.dumps({
                    "id": "20210001",
                    "password": "test_password"
                })
            }
            
            # Call lambda_handler
            result = lambda_handler(event, None)
            
            # Verify response
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["studentId"] == "20210001"
            assert body["name"] == "홍길동"
            assert body["department"] == "컴퓨터공학부"
            assert body["grade"] == 3
            assert body["year"] == 20

    def test_lambda_handler_login_error(self):
        """Test lambda_handler with login error"""
        with patch("v2.auth.login.SejongPortalSession") as mock_session_class:
            # Mock session to raise PortalLoginError
            mock_session_class.side_effect = PortalLoginError(401, "아이디나 비밀번호가 일치하지 않습니다.")
            
            # Create event
            event = {
                "body": json.dumps({
                    "id": "20210001",
                    "password": "wrong_password"
                })
            }
            
            # Call lambda_handler
            result = lambda_handler(event, None)
            
            # Verify error response
            assert result["statusCode"] == 401
            body = json.loads(result["body"])
            assert "아이디나 비밀번호가 일치하지 않습니다" in body["result"]

    def test_lambda_handler_server_unavailable(self):
        """Test lambda_handler when server is unavailable"""
        with patch("v2.auth.login.SejongPortalSession") as mock_session_class:
            # Mock session to raise SejongServerNotAvailableError
            mock_session_class.side_effect = SejongServerNotAvailableError()
            
            # Create event
            event = {
                "body": json.dumps({
                    "id": "20210001",
                    "password": "test_password"
                })
            }
            
            # Call lambda_handler
            result = lambda_handler(event, None)
            
            # Verify error response
            assert result["statusCode"] == 503
            body = json.loads(result["body"])
            assert "세종대학교 서버가 응답이 없습니다" in body["result"]

    def test_lambda_handler_missing_credentials(self):
        """Test lambda_handler with missing credentials"""
        # Create event with missing password
        event = {
            "body": json.dumps({
                "id": "20210001"
            })
        }
        
        # Call lambda_handler
        result = lambda_handler(event, None)
        
        # Verify error response
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid student_id or password" in body["message"]

    def test_lambda_handler_invalid_json(self):
        """Test lambda_handler with invalid JSON in body"""
        # Create event with invalid JSON
        event = {
            "body": "invalid json"
        }
        
        # Call lambda_handler - should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            lambda_handler(event, None)


class TestGetUserInfo:
    """Test get_user_info function"""

    def test_get_user_info_success(self):
        """Test successful user info retrieval"""
        with patch("v2.auth.login.SejongPortalSession") as mock_session_class:
            # Mock session instance
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock portal page response
            mock_response = MagicMock()
            mock_response.text = """
            <html>
                <div class="uInfoBox">
                    <span>김철수</span>
                    <dd>경영학과</dd>
                    <dd>2</dd>
                </div>
            </html>
            """
            mock_session.get.return_value = mock_response
            
            # Call get_user_info
            status_code, info = get_user_info("20220002", "password123")
            
            # Verify response
            assert status_code == 200
            assert info["studentId"] == "20220002"
            assert info["name"] == "김철수"
            assert info["department"] == "경영학과"
            assert info["grade"] == 2
            assert info["year"] == 20

    def test_get_user_info_missing_info_area(self):
        """Test get_user_info when info area is missing"""
        with patch("v2.auth.login.SejongPortalSession") as mock_session_class:
            # Mock session instance
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock portal page response without info area
            mock_response = MagicMock()
            mock_response.text = "<html><body>No info</body></html>"
            mock_session.get.return_value = mock_response
            
            # Call get_user_info
            status_code, info = get_user_info("20230003", "password123")
            
            # Verify response with defaults
            assert status_code == 200
            assert info["studentId"] == "20230003"
            assert info["name"] == ""
            assert info["department"] == ""
            assert info["grade"] == 1
            assert info["year"] == 20

    def test_get_user_info_login_error(self):
        """Test get_user_info when login fails"""
        with patch("v2.auth.login.SejongPortalSession") as mock_session_class:
            # Mock session to raise PortalLoginError
            mock_session_class.side_effect = PortalLoginError(401, "로그인 실패")
            
            # Should raise PortalLoginError
            with pytest.raises(PortalLoginError):
                get_user_info("20210001", "wrong_password")
