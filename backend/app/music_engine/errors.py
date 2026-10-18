"""Lỗi có cấu trúc của Music Engine.

Nguyên tắc (báo cáo v1 §6.1): từ chối rõ ràng thay vì đoán. Mọi đầu vào ngoài
phạm vi trả về một mã lỗi cố định, không bao giờ trả kết quả gần đúng.
"""


class MusicEngineError(ValueError):
    """Lỗi gốc. `code` là mã cố định để frontend/AI dịch sang lời giải thích."""

    code = "ENGINE_ERROR"

    def __init__(self, message: str, **details):
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


class InvalidPitch(MusicEngineError):
    code = "INVALID_PITCH"


class UnsupportedSpelling(MusicEngineError):
    """Dấu hóa vượt ±2 (SRS 4.4.1: accidental -2..+2)."""

    code = "UNSUPPORTED_SPELLING"


class InvalidInterval(MusicEngineError):
    code = "INVALID_INTERVAL"


class UnsupportedInterval(MusicEngineError):
    code = "UNSUPPORTED_INTERVAL"


class UnknownScaleType(MusicEngineError):
    code = "UNKNOWN_SCALE_TYPE"


class UnsupportedKey(MusicEngineError):
    code = "UNSUPPORTED_KEY"


class UnknownQuality(MusicEngineError):
    code = "UNKNOWN_QUALITY"


class InvalidChordSymbol(MusicEngineError):
    code = "INVALID_CHORD_SYMBOL"


class NoMatch(MusicEngineError):
    code = "NO_MATCH"


class NotDiatonic(MusicEngineError):
    code = "NOT_DIATONIC"


class NotSupportedInMvp(MusicEngineError):
    """Tính năng có trong nhạc lý nhưng đã quyết định để sau MVP (ví dụ giọng thứ ở K08)."""

    code = "NOT_SUPPORTED_IN_MVP"


class ConventionNotVerified(MusicEngineError):
    """Hồ sơ quy ước chưa có nguồn đã xác minh (ví dụ số La Mã jazz-pop)."""

    code = "CONVENTION_NOT_VERIFIED"


class InvalidRhythm(MusicEngineError):
    code = "INVALID_RHYTHM"
