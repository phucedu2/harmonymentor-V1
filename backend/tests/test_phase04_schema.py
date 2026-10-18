from app.db.base import Base
from app.db import models  # noqa: F401


def test_learning_contract_tables_registered():
    expected = {
        "users", "skills", "skill_prerequisites", "lessons", "lesson_blocks", "source_works",
        "lesson_sources", "exercises", "exercise_versions", "attempts", "attempt_errors",
        "lesson_progress", "review_items", "review_states", "review_attempts",
    }
    assert expected.issubset(set(Base.metadata.tables))
