from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth.deps import require_admin
from ..db.models import User

# Mọi route /api/v1/admin/* gắn require_admin ở cấp router để không route nào quên kiểm tra quyền.
router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/ping")
def admin_ping(user: User = Depends(require_admin)):
    return {"ok": True, "user_id": user.id}
