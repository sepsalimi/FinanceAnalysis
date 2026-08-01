"""Overall assessment status computation for canonical events."""

from app.models.enums import EventType, OverallAssessmentStatus
from app.models.events import CanonicalFinancialEvent


def compute_overall_status(event: CanonicalFinancialEvent) -> str:
    if event.overall_assessment_status == OverallAssessmentStatus.EXCLUDED.value:
        return OverallAssessmentStatus.EXCLUDED.value
    if event.overall_assessment_status == OverallAssessmentStatus.FAILED.value:
        return OverallAssessmentStatus.FAILED.value

    if not event.event_date or event.confirmed_amount is None:
        return OverallAssessmentStatus.FAILED.value

    if event.event_type in {EventType.UNKNOWN.value} and not event.confirmed_category_id:
        return OverallAssessmentStatus.UNASSESSED.value

    if not event.confirmed_category_id and event.event_type != EventType.TRANSFER.value:
        return OverallAssessmentStatus.PENDING_CATEGORY.value

    if event.splitwise_match_status == "needs_review":
        return OverallAssessmentStatus.PENDING_MATCH.value

    if event.duplicate_status == "possible":
        return OverallAssessmentStatus.NEEDS_REVIEW.value

    if event.transfer_status == "possible":
        return OverallAssessmentStatus.NEEDS_REVIEW.value

    if event.review_reason and (event.llm_confidence or 0) < 0.9:
        if event.confirmed_category_id:
            return OverallAssessmentStatus.ASSESSED_WITH_WARNING.value
        return OverallAssessmentStatus.NEEDS_REVIEW.value

    required_ok = all(
        [
            event.event_date is not None,
            event.confirmed_amount is not None,
            event.event_type != EventType.UNKNOWN.value,
            event.confirmed_category_id is not None or event.event_type == EventType.TRANSFER.value,
            event.ownership_allocation is not None,
            event.duplicate_status in {"unknown", "none", "confirmed_unique"},
            event.transfer_status in {"unknown", "none", "likely", "confirmed", "not_transfer"},
            event.refund_status in {"unknown", "none", "likely", "confirmed", "not_refund"},
            event.reimbursement_status
            in {"unknown", "none", "likely", "confirmed", "not_reimbursement"},
        ]
    )
    if required_ok:
        return OverallAssessmentStatus.ASSESSED.value
    return OverallAssessmentStatus.NEEDS_REVIEW.value
