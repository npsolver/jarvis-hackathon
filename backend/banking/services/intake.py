"""
2.1 Shared intake orchestration used by the user APIs (and by the CSV
migration script, which submits rows through the exact same path).

Flow: review -> valid? migrate : send to human review table.
"""

from dataclasses import dataclass

from banking.models import HumanReview
from banking.services.migration import migrate_account, migrate_transaction
from banking.services.review import review_account, review_transaction
from banking.services.review_queue import send_to_review


@dataclass
class IntakeResult:
    status: str  # 'MIGRATED' or 'REVIEW'
    entity: object = None
    review: HumanReview = None
    reasons: list = None


def submit_account(raw_payload: dict, source=HumanReview.Source.API) -> IntakeResult:
    result = review_account(raw_payload)
    if result.is_valid:
        account = migrate_account(result.cleaned)
        return IntakeResult(status='MIGRATED', entity=account)
    review = send_to_review(HumanReview.EntityType.ACCOUNT, raw_payload, result.reasons, source)
    return IntakeResult(status='REVIEW', review=review, reasons=result.reasons)


def submit_transaction(raw_payload: dict, source=HumanReview.Source.API) -> IntakeResult:
    result = review_transaction(raw_payload)
    if result.is_valid:
        tx = migrate_transaction(result.cleaned)
        return IntakeResult(status='MIGRATED', entity=tx)
    review = send_to_review(HumanReview.EntityType.TRANSACTION, raw_payload, result.reasons, source)
    return IntakeResult(status='REVIEW', review=review, reasons=result.reasons)
