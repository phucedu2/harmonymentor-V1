"""Tiện ích test: tạo người dùng trực tiếp trong CSDL và cấp access token, bỏ qua bước đăng nhập."""

from __future__ import annotations

from app.auth.security import create_access_token


def auth(user_id: str, role: str = "learner") -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id, role)}"}


def correct_answer(item: dict):
    """Đáp án đúng chuẩn của một câu trong curriculum_specs, dùng để test luồng hoàn thành bài."""
    key = item["answer_key"]
    if "expected" in key:
        expected = key["expected"]
        return " ".join(expected) if isinstance(expected, list) else expected
    return key["accepted"][0]


def answer_lesson_correctly(client, lesson_id: str, headers: dict[str, str]) -> None:
    """Từ v0.5.4 chỉ hoàn thành được bài khi mọi câu đã đúng ít nhất một lần."""
    from app.content.curriculum_specs import lesson_by_id

    lesson = client.get(f"/api/v1/lessons/{lesson_id}").json()
    by_id = {item["id"]: item for item in lesson_by_id(lesson_id)["exercises"]}
    for exercise in lesson["exercises"]:
        response = client.post("/api/v1/attempts", headers=headers, json={
            "exercise_version_id": exercise["version_id"], "answer": correct_answer(by_id[exercise["id"]]),
        })
        assert response.status_code == 200 and response.json()["correct"], (exercise["id"], response.json())
