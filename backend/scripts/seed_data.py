from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.ai_suggestion import AISuggestion
from app.models.knowledge_doc import KnowledgeDoc
from app.models.ticket import Ticket
from app.models.ticket_message import TicketMessage
from app.models.user import User
from app.services.knowledge_service import KnowledgeService
from app.services.ticket_similarity_service import TicketSimilarityService
from app.services.user_service import UserService


SEED_TICKET_SOURCE = "seed_demo"


@dataclass(frozen=True)
class KnowledgeSeed:
    key: str
    title: str
    file_name: str
    content: str


@dataclass(frozen=True)
class SuggestionSeed:
    status: str
    suggested_content: str
    reasoning_summary: str
    confidence: float
    source_doc_keys: tuple[str, ...]
    reviewer_role: str | None = None
    final_content: str | None = None
    reject_reason: str | None = None


@dataclass(frozen=True)
class TicketSeed:
    title: str
    content: str
    customer_name: str
    customer_email: str
    category: str
    priority: str
    sentiment: str
    status: str
    recommended_department: str
    ai_summary: str
    assigned_role: str | None
    created_days_ago: int
    updated_days_ago: int
    closed_days_ago: int | None
    messages: tuple[dict[str, str], ...]
    suggestions: tuple[SuggestionSeed, ...] = ()


KNOWLEDGE_SEEDS: tuple[KnowledgeSeed, ...] = (
    KnowledgeSeed(
        key="payment_sop",
        title="Payment Incident SOP",
        file_name="seed_demo_payment_incident_sop.md",
        content="""# Payment Incident SOP

## Scope
Use this SOP when a customer reports duplicate charges, payment captured but order still pending, or renewal billing mismatches.

## First-response checklist
1. Confirm the workspace ID, payment timestamp, amount, and payment channel.
2. Verify whether the order state is still `pending`, `awaiting_capture`, or already `active`.
3. Check whether more than one successful authorization exists for the same billing period.

## Resolution policy
- If money was captured but entitlement did not activate, manually re-run the order sync and confirm service access.
- If duplicate capture is confirmed, create a refund request for the extra charge and tell the customer the reversal is under billing review.
- If an enterprise renewal is blocked, mark the case as urgent and route it to billing for same-day handling.

## Customer communication notes
- Acknowledge the payment issue clearly.
- Never promise an immediate refund before billing validation.
- Quote the expected review window of 1-2 business days for duplicate charge reversals.
""",
    ),
    KnowledgeSeed(
        key="invoice_policy",
        title="Invoice Correction Policy",
        file_name="seed_demo_invoice_correction_policy.md",
        content="""# Invoice Correction Policy

## Supported corrections
- Legal company name updates
- VAT / tax ID fixes
- Billing address corrections
- PO reference additions for enterprise invoices

## Required evidence
1. Customer account email
2. Invoice number or order number
3. Correct legal entity details

## Turnaround expectations
- Standard invoice corrections should be completed within 1 business day.
- If tax treatment changes across countries, finance review is required before reissuing the invoice.

## Customer reply guidance
- Confirm that the original invoice will be voided if required by local compliance.
- Tell the customer the corrected PDF will be sent after finance validation.
""",
    ),
    KnowledgeSeed(
        key="refund_playbook",
        title="Refund Review Playbook",
        file_name="seed_demo_refund_review_playbook.md",
        content="""# Refund Review Playbook

## When to use
Use this playbook for cancellation refunds, duplicate charges, partial credits, or service-failure compensation requests.

## Review flow
1. Confirm subscription status and charge history.
2. Determine whether the request falls under a published refund window.
3. Check for duplicate fulfillment or delayed activation.
4. Route high-value or policy exception refunds to billing approval.

## Decision guidance
- Duplicate charges are normally refundable after billing confirms the extra capture.
- Delayed activation may qualify for a partial service credit if the customer kept the subscription active.
- Out-of-policy refunds require manual reviewer approval and should not be auto-promised.

## Communication notes
- Be explicit about review status.
- State whether the case is in validation, approved, or declined.
- Approved refunds should mention the payment-provider settlement window of 5-10 business days.
""",
    ),
)


HISTORICAL_TICKET_SEEDS: tuple[TicketSeed, ...] = (
    TicketSeed(
        title="Payment captured but order stayed pending for APAC customer",
        content=(
            "The customer completed a card payment for an enterprise add-on, but the order still shows "
            "pending and the seats never activated. Finance confirmed the payment was captured."
        ),
        customer_name="Alicia Wong",
        customer_email="alicia.wong@northwind-apac.example",
        category="payment",
        priority="high",
        sentiment="negative",
        status="resolved",
        recommended_department="billing",
        ai_summary="Captured payment did not activate the purchased enterprise add-on.",
        assigned_role="agent",
        created_days_ago=28,
        updated_days_ago=27,
        closed_days_ago=27,
        messages=(
            {
                "sender_type": "customer",
                "sender_name": "Alicia Wong",
                "content": "We paid for the add-on this morning, but the workspace still shows pending and our seats are missing.",
            },
            {
                "sender_type": "agent",
                "sender_name": "agent",
                "content": "We confirmed the captured payment, re-ran the order sync, and restored the missing seats for the customer.",
            },
        ),
        suggestions=(
            SuggestionSeed(
                status="approved",
                suggested_content=(
                    "We confirmed your payment was captured correctly and found that the order sync did not finish. "
                    "Our team has reprocessed the activation and your enterprise seats are now restored."
                ),
                reasoning_summary="Payment SOP matched a captured-payment-without-activation scenario.",
                confidence=0.94,
                source_doc_keys=("payment_sop",),
                reviewer_role="agent",
                final_content=(
                    "We confirmed your payment was captured correctly and reprocessed the activation. "
                    "Your enterprise seats are now available, and we will monitor the order for the next billing cycle."
                ),
            ),
        ),
    ),
    TicketSeed(
        title="Refund still missing 7 days after cancellation",
        content=(
            "A customer canceled within the refund window, but says the refund has not arrived after seven days. "
            "They are asking for a status update and confirmation of the payment-provider timeline."
        ),
        customer_name="Marco Silva",
        customer_email="marco.silva@orion-logistics.example",
        category="refund",
        priority="high",
        sentiment="angry",
        status="closed",
        recommended_department="billing",
        ai_summary="Customer wants an update on a refund that is still pending after cancellation.",
        assigned_role="agent",
        created_days_ago=24,
        updated_days_ago=22,
        closed_days_ago=22,
        messages=(
            {
                "sender_type": "customer",
                "sender_name": "Marco Silva",
                "content": "We canceled within policy, but the money has not shown up after seven days. This is becoming urgent.",
            },
            {
                "sender_type": "agent",
                "sender_name": "agent",
                "content": "Billing confirmed the refund approval and shared the 5-10 business day settlement timeline with the customer.",
            },
        ),
        suggestions=(
            SuggestionSeed(
                status="edited",
                suggested_content=(
                    "Your refund request has been approved and is moving through the payment-provider settlement process."
                ),
                reasoning_summary="Refund playbook matched an approved cancellation refund still in settlement.",
                confidence=0.91,
                source_doc_keys=("refund_playbook",),
                reviewer_role="agent",
                final_content=(
                    "Your refund has been approved and is already in the payment-provider settlement stage. "
                    "Most banks post the reversal within 5-10 business days, and we will continue to monitor it until completion."
                ),
            ),
        ),
    ),
    TicketSeed(
        title="VAT invoice missing company tax ID after billing export",
        content=(
            "The invoice PDF was generated without the customer tax ID, so finance cannot book the expense before month-end close."
        ),
        customer_name="Hana Becker",
        customer_email="hana.becker@atlas-energy.example",
        category="invoice",
        priority="medium",
        sentiment="negative",
        status="resolved",
        recommended_department="finance",
        ai_summary="Customer needs a corrected invoice with the legal tax ID included.",
        assigned_role="agent",
        created_days_ago=18,
        updated_days_ago=17,
        closed_days_ago=17,
        messages=(
            {
                "sender_type": "customer",
                "sender_name": "Hana Becker",
                "content": "The invoice PDF is missing our company tax ID, so accounting cannot process it.",
            },
            {
                "sender_type": "agent",
                "sender_name": "agent",
                "content": "Finance reissued the invoice with the correct tax ID and sent the corrected PDF to the customer.",
            },
        ),
        suggestions=(
            SuggestionSeed(
                status="approved",
                suggested_content=(
                    "We can reissue the invoice after validating the corrected legal entity details and tax ID."
                ),
                reasoning_summary="Invoice correction policy covers tax ID fixes and reissued PDFs.",
                confidence=0.89,
                source_doc_keys=("invoice_policy",),
                reviewer_role="agent",
                final_content=(
                    "We validated the corrected legal entity details and reissued the invoice with the proper tax ID. "
                    "The updated PDF has been sent to your billing contact."
                ),
            ),
        ),
    ),
)


CURRENT_TICKET_SEEDS: tuple[TicketSeed, ...] = (
    TicketSeed(
        title="Enterprise renewal charged twice and finance team needs reversal",
        content=(
            "The customer says their annual renewal was captured twice this morning. They need a billing reversal "
            "and confirmation that the duplicate charge will not affect service continuity."
        ),
        customer_name="Lena Foster",
        customer_email="lena.foster@greenfield-holdings.example",
        category="payment",
        priority="urgent",
        sentiment="angry",
        status="waiting_review",
        recommended_department="billing",
        ai_summary="Urgent duplicate-charge complaint on an enterprise annual renewal.",
        assigned_role="agent",
        created_days_ago=2,
        updated_days_ago=1,
        closed_days_ago=None,
        messages=(
            {
                "sender_type": "customer",
                "sender_name": "Lena Foster",
                "content": "We were charged twice for the same renewal this morning. Finance needs a reversal immediately.",
            },
        ),
        suggestions=(
            SuggestionSeed(
                status="draft",
                suggested_content=(
                    "We are validating the duplicate annual-renewal capture with billing and will update you as soon as the reversal is approved."
                ),
                reasoning_summary="Payment SOP suggests cautious wording until duplicate capture is confirmed.",
                confidence=0.87,
                source_doc_keys=("payment_sop", "refund_playbook"),
            ),
        ),
    ),
    TicketSeed(
        title="Need corrected invoice before month-end finance close",
        content=(
            "The enterprise customer needs a corrected invoice with an updated billing address and PO reference before finance close tomorrow."
        ),
        customer_name="Priya Raman",
        customer_email="priya.raman@cedar-ventures.example",
        category="invoice",
        priority="high",
        sentiment="negative",
        status="open",
        recommended_department="finance",
        ai_summary="Invoice correction request is time-sensitive because finance close is tomorrow.",
        assigned_role="agent",
        created_days_ago=1,
        updated_days_ago=1,
        closed_days_ago=None,
        messages=(
            {
                "sender_type": "customer",
                "sender_name": "Priya Raman",
                "content": "Please correct the billing address and add our PO before tomorrow's finance close.",
            },
        ),
        suggestions=(
            SuggestionSeed(
                status="approved",
                suggested_content=(
                    "We can update the billing address and PO reference after validating the corrected invoice details."
                ),
                reasoning_summary="Invoice policy supports address and PO updates with one-business-day turnaround.",
                confidence=0.88,
                source_doc_keys=("invoice_policy",),
                reviewer_role="admin",
                final_content=(
                    "We have queued the billing address and PO correction with finance and will send the corrected invoice PDF as soon as validation completes."
                ),
            ),
        ),
    ),
    TicketSeed(
        title="Customer requests partial refund after delayed activation",
        content=(
            "The customer kept the subscription active but is asking for a partial refund because service activation was delayed for two days."
        ),
        customer_name="Noah Kim",
        customer_email="noah.kim@harbor-digital.example",
        category="refund",
        priority="high",
        sentiment="negative",
        status="in_progress",
        recommended_department="billing",
        ai_summary="Customer seeks a partial refund tied to delayed activation.",
        assigned_role="agent",
        created_days_ago=4,
        updated_days_ago=1,
        closed_days_ago=None,
        messages=(
            {
                "sender_type": "customer",
                "sender_name": "Noah Kim",
                "content": "Activation was delayed for two days. We kept the service, but want a partial refund or service credit.",
            },
        ),
        suggestions=(
            SuggestionSeed(
                status="rejected",
                suggested_content=(
                    "We are unable to issue a refund because the subscription remained active."
                ),
                reasoning_summary="Refund playbook requires manual approval for partial credits after delayed activation.",
                confidence=0.71,
                source_doc_keys=("refund_playbook",),
                reviewer_role="admin",
                reject_reason="The wording was too absolute. Billing wants a manual review before declining a partial credit request.",
            ),
        ),
    ),
    TicketSeed(
        title="Account owner cannot access billing portal after SSO migration",
        content=(
            "After the SSO migration, the account owner can sign in to the main product but loses access when opening the billing portal."
        ),
        customer_name="Mateo Alvarez",
        customer_email="mateo.alvarez@silverline-health.example",
        category="account",
        priority="medium",
        sentiment="negative",
        status="open",
        recommended_department="customer_support",
        ai_summary="Account owner is blocked from billing access after SSO migration.",
        assigned_role="agent",
        created_days_ago=3,
        updated_days_ago=2,
        closed_days_ago=None,
        messages=(
            {
                "sender_type": "customer",
                "sender_name": "Mateo Alvarez",
                "content": "SSO works for the app, but the billing portal throws us back to the sign-in screen.",
            },
        ),
        suggestions=(),
    ),
)


def now_utc() -> datetime:
    return datetime.now(UTC)


def build_preview(content: str, max_length: int = 180) -> str:
    normalized = " ".join(content.split()).strip()
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3]}..."


def write_knowledge_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_demo_users(db) -> dict[str, User]:
    UserService(db).ensure_default_users()
    users = db.scalars(select(User)).all()
    return {user.role: user for user in users}


def upsert_knowledge_doc(db, knowledge_service: KnowledgeService, seed: KnowledgeSeed, uploader: User) -> KnowledgeDoc:
    upload_dir = Path(knowledge_service.settings.knowledge_upload_dir).resolve()
    file_path = upload_dir / seed.file_name
    write_knowledge_file(file_path, seed.content)

    existing = db.scalar(
        select(KnowledgeDoc).where(KnowledgeDoc.file_name == seed.file_name)
    )
    if existing is None:
        document = KnowledgeDoc(
            title=seed.title,
            file_name=seed.file_name,
            file_type=file_path.suffix.removeprefix("."),
            file_path=str(file_path),
            content=seed.content,
            doc_type="knowledge_base",
            status="uploaded",
            uploaded_by=uploader.id,
            error_message=None,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
    else:
        document = existing
        document.title = seed.title
        document.file_type = file_path.suffix.removeprefix(".")
        document.file_path = str(file_path)
        document.content = seed.content
        document.doc_type = "knowledge_base"
        document.status = "uploaded"
        document.uploaded_by = uploader.id
        document.error_message = None
        db.add(document)
        db.commit()
        db.refresh(document)

    processed = knowledge_service.process_document(document.id)
    processed.created_at = now_utc() - timedelta(days=14)
    processed.updated_at = now_utc() - timedelta(days=1)
    db.add(processed)
    db.commit()
    db.refresh(processed)
    return processed


def upsert_ticket(
    db,
    similarity_service: TicketSimilarityService,
    seed: TicketSeed,
    *,
    created_by: User,
    assigned_to: User | None,
) -> Ticket:
    existing = db.scalar(
        select(Ticket).where(
            Ticket.source == SEED_TICKET_SOURCE,
            Ticket.title == seed.title,
        )
    )

    timestamp_now = now_utc()
    closed_at = timestamp_now - timedelta(days=seed.closed_days_ago) if seed.closed_days_ago is not None else None

    if existing is None:
        ticket = Ticket(
            title=seed.title,
            content=seed.content,
            customer_name=seed.customer_name,
            customer_email=seed.customer_email,
            category=seed.category,
            priority=seed.priority,
            sentiment=seed.sentiment,
            status=seed.status,
            source=SEED_TICKET_SOURCE,
            ai_summary=seed.ai_summary,
            recommended_department=seed.recommended_department,
            assigned_to=assigned_to.id if assigned_to else None,
            created_by=created_by.id,
            closed_at=closed_at,
        )
        db.add(ticket)
    else:
        ticket = existing
        ticket.content = seed.content
        ticket.customer_name = seed.customer_name
        ticket.customer_email = seed.customer_email
        ticket.category = seed.category
        ticket.priority = seed.priority
        ticket.sentiment = seed.sentiment
        ticket.status = seed.status
        ticket.source = SEED_TICKET_SOURCE
        ticket.ai_summary = seed.ai_summary
        ticket.recommended_department = seed.recommended_department
        ticket.assigned_to = assigned_to.id if assigned_to else None
        ticket.created_by = created_by.id
        ticket.closed_at = closed_at
        db.add(ticket)

    db.commit()
    db.refresh(ticket)

    ticket.created_at = timestamp_now - timedelta(days=seed.created_days_ago)
    ticket.updated_at = timestamp_now - timedelta(days=seed.updated_days_ago)
    ticket.closed_at = closed_at
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    similarity_service.ensure_ticket_embedding(ticket)
    db.refresh(ticket)
    return ticket


def reseed_ticket_messages(db, ticket: Ticket, messages: tuple[dict[str, str], ...]) -> None:
    db.execute(delete(TicketMessage).where(TicketMessage.ticket_id == ticket.id))
    db.commit()

    base_time = ticket.created_at
    for index, message_seed in enumerate(messages):
        message_time = base_time + timedelta(hours=index)
        message = TicketMessage(
            ticket_id=ticket.id,
            sender_type=message_seed["sender_type"],
            sender_name=message_seed["sender_name"],
            content=message_seed["content"],
        )
        message.created_at = message_time
        message.updated_at = message_time
        db.add(message)

    db.commit()


def build_sources_json(
    doc_chunks: dict[str, list[dict[str, Any]]],
    doc_keys: tuple[str, ...],
    *,
    score: float,
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for doc_key in doc_keys:
        chunk_candidates = doc_chunks.get(doc_key, [])
        if not chunk_candidates:
            continue
        chunk = chunk_candidates[0]
        sources.append(
            {
                "doc_id": chunk["doc_id"],
                "chunk_id": chunk["chunk_id"],
                "chunk_index": chunk["chunk_index"],
                "content_preview": chunk["content_preview"],
                "score": score,
            }
        )
    return sources


def reseed_ticket_suggestions(
    db,
    ticket: Ticket,
    suggestion_seeds: tuple[SuggestionSeed, ...],
    *,
    users_by_role: dict[str, User],
    doc_chunks: dict[str, list[dict[str, Any]]],
) -> None:
    db.execute(delete(AISuggestion).where(AISuggestion.ticket_id == ticket.id))
    db.commit()

    for index, suggestion_seed in enumerate(suggestion_seeds):
        created_time = ticket.created_at + timedelta(hours=2 + index)
        reviewer = users_by_role.get(suggestion_seed.reviewer_role or "") if suggestion_seed.reviewer_role else None
        suggestion = AISuggestion(
            ticket_id=ticket.id,
            suggestion_type="reply",
            source_workflow="single_agent_rag",
            source_run_id=None,
            suggested_content=suggestion_seed.suggested_content,
            reasoning_summary=suggestion_seed.reasoning_summary,
            sources_json=build_sources_json(
                doc_chunks,
                suggestion_seed.source_doc_keys,
                score=round(min(0.99, suggestion_seed.confidence), 3),
            ),
            confidence=suggestion_seed.confidence,
            status=suggestion_seed.status,
            reviewed_by=reviewer.id if reviewer and suggestion_seed.status != "draft" else None,
            reviewed_at=created_time + timedelta(hours=1) if reviewer and suggestion_seed.status != "draft" else None,
            final_content=suggestion_seed.final_content,
            reject_reason=suggestion_seed.reject_reason,
        )
        suggestion.created_at = created_time
        suggestion.updated_at = (
            created_time + timedelta(hours=1)
            if suggestion.status != "draft"
            else created_time
        )
        db.add(suggestion)

    db.commit()


def collect_doc_chunks(
    db,
    knowledge_service: KnowledgeService,
    seeds: tuple[KnowledgeSeed, ...],
) -> dict[str, list[dict[str, Any]]]:
    doc_chunks: dict[str, list[dict[str, Any]]] = {}
    for seed in seeds:
        document = db.scalar(select(KnowledgeDoc).where(KnowledgeDoc.file_name == seed.file_name))
        if document is None:
            continue
        chunks = knowledge_service.list_chunks(document.id)
        doc_chunks[seed.key] = [
            {
                "doc_id": chunk.doc_id,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content_preview": build_preview(chunk.content),
            }
            for chunk in chunks
        ]
    return doc_chunks


def summarize_seed_state(db) -> dict[str, Any]:
    knowledge_docs = db.scalars(
        select(KnowledgeDoc).where(KnowledgeDoc.file_name.like("seed_demo_%"))
    ).all()
    tickets = db.scalars(
        select(Ticket).where(Ticket.source == SEED_TICKET_SOURCE)
    ).all()
    suggestions = db.scalars(
        select(AISuggestion).where(AISuggestion.ticket_id.in_([ticket.id for ticket in tickets] or [-1]))
    ).all()
    return {
        "knowledge_docs": len(knowledge_docs),
        "tickets": len(tickets),
        "resolved_or_closed_tickets": sum(ticket.status in {"resolved", "closed"} for ticket in tickets),
        "open_workload_tickets": sum(ticket.status in {"open", "waiting_review", "in_progress"} for ticket in tickets),
        "ai_suggestions": len(suggestions),
    }


def main() -> None:
    database_url = init_db()
    print(f"Seeding demo data into: {database_url}")

    with SessionLocal() as db:
        users_by_role = ensure_demo_users(db)
        admin_user = users_by_role["admin"]
        agent_user = users_by_role["agent"]

        knowledge_service = KnowledgeService(db)
        similarity_service = TicketSimilarityService(db)

        for knowledge_seed in KNOWLEDGE_SEEDS:
            upsert_knowledge_doc(db, knowledge_service, knowledge_seed, admin_user)

        doc_chunks = collect_doc_chunks(db, knowledge_service, KNOWLEDGE_SEEDS)

        all_ticket_seeds = HISTORICAL_TICKET_SEEDS + CURRENT_TICKET_SEEDS
        for ticket_seed in all_ticket_seeds:
            assigned_user = agent_user if ticket_seed.assigned_role == "agent" else None
            ticket = upsert_ticket(
                db,
                similarity_service,
                ticket_seed,
                created_by=admin_user,
                assigned_to=assigned_user,
            )
            reseed_ticket_messages(db, ticket, ticket_seed.messages)
            reseed_ticket_suggestions(
                db,
                ticket,
                ticket_seed.suggestions,
                users_by_role=users_by_role,
                doc_chunks=doc_chunks,
            )

        summary = summarize_seed_state(db)
        print("Seed summary:")
        for key, value in summary.items():
            print(f"  - {key}: {value}")


if __name__ == "__main__":
    main()
