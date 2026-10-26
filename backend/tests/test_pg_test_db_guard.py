"""Điều kiện an toàn của CSDL test PostgreSQL (pg_test_db.py). Hàm thuần, chạy được không cần PostgreSQL."""

from __future__ import annotations

import pytest

from tests.pg_test_db import create_isolated_engine, drop_isolated_schema, new_schema_name, unsafe_reason

PG = "postgresql+psycopg://hm:hm@127.0.0.1:55432/"


@pytest.mark.parametrize("test_url, app_url, expected", [
    ("", "sqlite:///./harmonymentor_dev.db", "Chưa đặt"),
    ("không phải url", "", "không đúng định dạng"),
    ("sqlite:///./x_test.db", "", "phải trỏ tới PostgreSQL"),
    (PG + "harmony", "", "kết thúc bằng _test"),
    (PG + "harmony_test_backup", "", "kết thúc bằng _test"),
    # Cùng CSDL với app: viết khác host (localhost/127.0.0.1) hoặc bỏ cổng mặc định vẫn bị chặn.
    (PG + "harmony_test", PG + "harmony_test", "trùng CSDL của ứng dụng"),
    ("postgresql+psycopg://a:b@localhost:55432/harmony_test", PG + "harmony_test", "trùng CSDL của ứng dụng"),
    ("postgresql://a:b@db/harmony_test", "postgresql+psycopg://x:y@db:5432/harmony_test", "trùng CSDL của ứng dụng"),
])
def test_unsafe_reason_refuses(test_url, app_url, expected):
    reason = unsafe_reason(test_url, app_url)
    assert reason is not None and expected in reason


@pytest.mark.parametrize("app_url", [
    "sqlite:///./harmonymentor_dev.db",
    "",
    PG + "harmony",                                     # CSDL app khác tên
    "postgresql+psycopg://hm:hm@127.0.0.1:5432/harmony_test",  # cùng tên nhưng khác cổng (máy chủ khác)
])
def test_unsafe_reason_accepts_separate_test_database(app_url):
    assert unsafe_reason(PG + "harmony_test", app_url) is None


@pytest.mark.parametrize("schema", ["public", "information_schema", "hm_pgtest_", "hm_pgtest_XYZ",
                                    'hm_pgtest_0123456789ab"; DROP SCHEMA public; --'])
def test_schema_helpers_refuse_names_not_created_by_tests(schema):
    # Kiểm tra tên trước khi kết nối, nên URL không cần trỏ tới máy chủ thật.
    with pytest.raises(ValueError):
        drop_isolated_schema(PG + "harmony_test", schema)
    with pytest.raises(ValueError):
        create_isolated_engine(PG + "harmony_test", schema)


def test_new_schema_names_are_random_and_valid():
    names = {new_schema_name() for _ in range(50)}
    assert len(names) == 50
    assert all(name.startswith("hm_pgtest_") and len(name) == len("hm_pgtest_") + 12 for name in names)
