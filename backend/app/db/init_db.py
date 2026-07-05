from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.session import engine
from app.services.user_service import UserService
from app.db.session import SessionLocal
from app import models  # noqa: F401


def init_db() -> str:
    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))

    Base.metadata.create_all(bind=engine)
    sync_ticket_ai_columns()
    sync_ai_suggestion_review_columns()
    sync_ai_suggestion_source_workflow()
    sync_ticket_embedding_table()
    seed_default_users()
    return str(engine.url)


def seed_default_users() -> None:
    db = SessionLocal()
    try:
        UserService(db).ensure_default_users()
    finally:
        db.close()


def sync_ticket_ai_columns() -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "tickets" not in table_names:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("tickets")}
    statements: list[str] = []

    if "sentiment" not in existing_columns:
        statements.append(
            "ALTER TABLE tickets ADD COLUMN sentiment VARCHAR(50) NOT NULL DEFAULT 'neutral'"
        )
    if "ai_summary" not in existing_columns:
        statements.append(
            "ALTER TABLE tickets ADD COLUMN ai_summary TEXT NULL"
        )
    if "recommended_department" not in existing_columns:
        statements.append(
            "ALTER TABLE tickets ADD COLUMN recommended_department VARCHAR(100) NULL"
        )

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def sync_ai_suggestion_review_columns() -> None:
    inspector = inspect(engine)
    if "ai_suggestions" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("ai_suggestions")}
    statements: list[str] = []

    if "reviewed_by" not in existing_columns:
        statements.append("ALTER TABLE ai_suggestions ADD COLUMN reviewed_by INT NULL")
    if "reviewed_at" not in existing_columns:
        statements.append("ALTER TABLE ai_suggestions ADD COLUMN reviewed_at VARCHAR(50) NULL")
    if "final_content" not in existing_columns:
        statements.append("ALTER TABLE ai_suggestions ADD COLUMN final_content TEXT NULL")
    if "reject_reason" not in existing_columns:
        statements.append("ALTER TABLE ai_suggestions ADD COLUMN reject_reason TEXT NULL")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def sync_ai_suggestion_source_workflow() -> None:
    inspector = inspect(engine)
    if "ai_suggestions" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("ai_suggestions")}
    if "source_workflow" in existing_columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE ai_suggestions "
                "ADD COLUMN source_workflow VARCHAR(50) NOT NULL DEFAULT 'single_agent'"
            )
        )


def sync_ticket_embedding_table() -> None:
    inspector = inspect(engine)
    if "ticket_embeddings" in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE ticket_embeddings (
                    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    ticket_id INT NOT NULL UNIQUE,
                    embedding_id VARCHAR(255) NOT NULL,
                    content_hash VARCHAR(64) NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX ix_ticket_embeddings_id (id),
                    INDEX ix_ticket_embeddings_ticket_id (ticket_id),
                    CONSTRAINT fk_ticket_embeddings_ticket_id
                        FOREIGN KEY (ticket_id) REFERENCES tickets (id)
                )
                """
            )
        )


if __name__ == "__main__":
    database_url = init_db()
    print(f"Initialized database for: {database_url}")
