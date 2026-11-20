"""Khối biến câu thành vector cho model định tuyến (ADR-030). Tách file riêng vì joblib lưu model theo đường dẫn
import của lớp: model đã lưu chỉ nạp lại được khi lớp E5Features và hàm prep vẫn ở đúng chỗ này."""

from __future__ import annotations

from sklearn.base import BaseEstimator, TransformerMixin

from ..ai.tutor.intent import _prep

_cache: dict[str, list[float]] = {}


def prep(text: str) -> str:
    # Giống model cũ: ghép câu có dấu và câu bỏ dấu để câu gõ không dấu vẫn khớp câu mẫu có dấu.
    return _prep(text)


class E5Features(BaseEstimator, TransformerMixin):
    """Vector e5-small (384 chiều) của câu hỏi, nhân với weight để cân với TF-IDF khi gộp.

    Luôn dùng bản e5 GỐC (local_embedder.DEFAULT_DIR), không theo LOCAL_EMBED_DIR, vì model được train trên vector
    của bản gốc; vector của bản tinh chỉnh khác hẳn sẽ làm sai nhãn. Không lưu đối tượng ONNX vào joblib."""

    def __init__(self, weight: float = 1.0):
        self.weight = weight

    def fit(self, x, y=None):
        return self

    def transform(self, x):
        import numpy as np

        from ..ai.embedder import EmbeddingUnavailable
        from ..ai.local_embedder import DEFAULT_DIR, get_local_embedder

        texts = list(x)
        missing = [t for t in dict.fromkeys(texts) if t not in _cache]
        if missing:
            emb = get_local_embedder(DEFAULT_DIR)
            if emb is None:
                raise EmbeddingUnavailable("local_model_missing")
            for t, v in zip(missing, emb.embed(missing, "RETRIEVAL_QUERY")):
                if len(_cache) > 20000:   # chặn cache phình mãi khi chạy lâu
                    _cache.clear()
                _cache[t] = v
        return np.array([_cache[t] for t in texts], dtype=np.float32) * self.weight
