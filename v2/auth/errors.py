class BaseError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

    def __str__(self):
        return self.message

class PortalLoginError(BaseError):
    def __init__(self, status_code, message):
        super().__init__(status_code, message)

class SejongServerNotAvailableError(BaseError):
    def __init__(self):
        super().__init__(503, "세종대학교 서버가 응답이 없습니다.")
