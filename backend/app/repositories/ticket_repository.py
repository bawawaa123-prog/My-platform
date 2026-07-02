'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-05-30 16:12:09
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-02 10:46:15
FilePath: \My-platform\backend\app\repositories\ticket_repository.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket


class TicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def list_all(self) -> list[Ticket]:
        statement = select(Ticket).order_by(Ticket.created_at.desc(), Ticket.id.desc())
        return list(self.db.scalars(statement).all())

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        statement = select(Ticket).where(Ticket.id == ticket_id)
        return self.db.scalar(statement)

    def list_resolved_or_closed_excluding(self, ticket_id: int) -> list[Ticket]:
        statement = (
            select(Ticket)
            .where(
                Ticket.id != ticket_id,
                Ticket.status.in_(("resolved", "closed")),
            )
            .order_by(Ticket.updated_at.desc(), Ticket.id.desc())
        )
        return list(self.db.scalars(statement).all())


    def list_filtered(
        self,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        assignee_id: int | None = None,
    ) -> list[Ticket]:
        statement = select(Ticket)

        if status:
            statement = statement.where(Ticket.status == status)
        if priority:
            statement = statement.where(Ticket.priority == priority)
        if category:
            statement = statement.where(Ticket.category == category)
        if assignee_id:
            statement = statement.where(Ticket.assignee_id == assignee_id)

        statement = statement.order_by(Ticket.created_at.desc(), Ticket.id.desc())
        return list(self.db.scalars(statement).all())


    def save(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket


