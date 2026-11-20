class RagError(RuntimeError):
    """Lỗi nạp/tìm kiếm mà người vận hành đọc được (thiếu mô hình, Qdrant chưa chạy, sai số chiều...)."""
