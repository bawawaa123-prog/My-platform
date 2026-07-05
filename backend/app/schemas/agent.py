'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-06-01 20:15:57
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-04 20:36:57
FilePath: \My-platform\backend\app\schemas\agent.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from pydantic import BaseModel, ConfigDict

from app.utils.datetime_utils import UTCDatetime


class AgentAuditTrailItemRead(BaseModel):
    agent_name: str
    action: str
    input_summary: str
    output_summary: str
    status: str
    timestamp: str


class AgentRunLogRead(BaseModel):
    id: int
    ticket_id: int
    run_id: str
    run_type: str
    status: str
    input_json: dict
    output_json: dict
    audit_trail_json: list[AgentAuditTrailItemRead]
    error_message: str | None
    created_by: int | None
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)

class AgentRunLogPage(BaseModel):
    items: list[AgentRunLogRead]
    total: int
    limit: int
    offset: int
