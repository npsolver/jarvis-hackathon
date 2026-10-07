"""
2.4 Send-to-review-table API.

Called by the review script whenever a record fails validation. Stores the
raw (un-cleaned) payload plus the reasons it was flagged, so a human admin
can see exactly what was submitted and why it was rejected.
"""

from banking.models import HumanReview


def send_to_review(entity_type: str, raw_payload: dict, reasons: list, source: str) -> HumanReview:
    return HumanReview.objects.create(
        entity_type=entity_type,
        payload=raw_payload,
        reasons=reasons,
        status=HumanReview.Status.PENDING,
        source=source,
    )
