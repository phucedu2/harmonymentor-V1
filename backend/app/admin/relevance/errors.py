class RelevanceError(Exception):
    """Lỗi người dùng đọc được: code ổn định (cho test/giao diện), message tiếng Việt."""

    def __init__(self, code: str, message: str, status: int = 422):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status
