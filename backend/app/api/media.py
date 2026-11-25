"""Phát file âm thanh ví dụ (FR-ADM-37). Công khai theo mã ngẫu nhiên: thẻ <audio> không gửi được token."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..core.errors import AppError
from ..db.models import MediaFile
from ..db.session import get_db

router = APIRouter(prefix="/api/v1/media", tags=["media"])


@router.get("/{media_id}")
def get_media(media_id: str, db: Session = Depends(get_db)):
    row = db.get(MediaFile, media_id)
    if row is None:
        raise AppError(404, "MEDIA_NOT_FOUND", "Không có file âm thanh này.")
    return Response(row.data, media_type=row.content_type, headers={"Cache-Control": "public, max-age=86400",
                                                                     "X-Content-Type-Options": "nosniff"})
