"""
2.5 Add/Remove API.

Called once an admin has looked at a HumanReview row.

- "remove": discard the record outright. Marks the review REJECTED; nothing
  is migrated.
- "add": (optionally with corrected fields merged in) sends the record back
  through the data review script. If it now passes, it goes to the data
  migration script. If it still fails, the same HumanReview row is updated
  in place (new reasons, new payload) -- i.e. sent back to the human review
  table -- rather than looping forever automatically.
"""

from dataclasses import dataclass

from django.utils import timezone

from banking.models import HumanReview
from banking.services.migration import migrate_account, migrate_transaction
from banking.services.review import review_account, review_transaction


@dataclass
class ResolutionResult:
    status: str  # 'MIGRATED', 'STILL_PENDING', or 'REJECTED'
    entity: object = None
    reasons: list = None


def remove_review(review: HumanReview, resolved_by: str = '') -> ResolutionResult:
    review.status = HumanReview.Status.REJECTED
    review.resolved_by = resolved_by
    review.resolved_at = timezone.now()
    review.save(update_fields=['status', 'resolved_by', 'resolved_at', 'updated_at'])
    return ResolutionResult(status='REJECTED')


def add_review(review: HumanReview, overrides: dict = None, resolved_by: str = '') -> ResolutionResult:
    candidate_payload = {**review.payload, **(overrides or {})}

    if review.entity_type == HumanReview.EntityType.ACCOUNT:
        result = review_account(candidate_payload)
    else:
        result = review_transaction(candidate_payload, exclude_transaction_id=review.payload.get('transactionId'))

    if result.is_valid:
        if review.entity_type == HumanReview.EntityType.ACCOUNT:
            entity = migrate_account(result.cleaned)
        else:
            entity = migrate_transaction(result.cleaned)
        review.status = HumanReview.Status.APPROVED
        review.payload = candidate_payload
        review.reasons = []
        review.resolved_by = resolved_by
        review.resolved_at = timezone.now()
        review.save(update_fields=['status', 'payload', 'reasons', 'resolved_by', 'resolved_at', 'updated_at'])
        return ResolutionResult(status='MIGRATED', entity=entity)

    # Still invalid -- sent back to the human review table for another pass.
    review.payload = candidate_payload
    review.reasons = result.reasons
    review.status = HumanReview.Status.PENDING
    review.save(update_fields=['payload', 'reasons', 'status', 'updated_at'])
    return ResolutionResult(status='STILL_PENDING', reasons=result.reasons)
