"""
统一 datetime 序列化工具。

SQLite 不保留 timezone 信息，读回的 datetime 可能是 naive（无时区）。
本模块确保所有序列化输出都带明确 UTC 时区（+00:00），
避免前端 new Date() 时将 UTC 时间误判为本地时间。
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BeforeValidator
from typing import Annotated


def ensure_utc(value: Any) -> Any:
    """如果 datetime 没有时区信息，默认当作 UTC 处理。

    适用于 Pydantic BeforeValidator，在数据进入模型前补全时区。
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    return value


# Pydantic 字段类型：替代 datetime，确保序列化输出带 +00:00
# 用法：created_at: UTCDatetime
UTCDatetime = Annotated[
    datetime,
    BeforeValidator(ensure_utc),
]
