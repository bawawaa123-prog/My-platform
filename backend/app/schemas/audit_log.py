'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-07-03 11:47:23
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-03 14:58:03
FilePath: \My-platform\backend\app\schemas\audit_log.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from pydantic import BaseModel, ConfigDict
from datetime import datetime




class AuditLogRead(BaseModel):
    id: int
    user_id: int
    action: str
    target_type: str
    target_id: int
    detail_json: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuditLogPage(BaseModel):
    items: list[AuditLogRead]
    total: int
    limit: int | None = None
    offset: int | None = None