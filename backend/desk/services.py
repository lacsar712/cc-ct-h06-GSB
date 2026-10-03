from django.conf import settings
from django.utils import timezone

from desk.models import OffsetSubmission


def evaluate_verdict(offset_um: int) -> str:
    if abs(offset_um) <= settings.OFFSET_TOLERANCE_UM:
        return OffsetSubmission.Verdict.PASS
    return OffsetSubmission.Verdict.FAIL


def verdict_reason(tool_code: str, offset_um: int, verdict: str) -> str:
    tol = settings.OFFSET_TOLERANCE_UM
    if verdict == OffsetSubmission.Verdict.PASS:
        return f"{tool_code} {offset_um}µm 在 ±{tol}µm 公差内，判定合格"
    if verdict == OffsetSubmission.Verdict.FAIL:
        return f"{tool_code} {offset_um}µm 超出 ±{tol}µm 公差，判定超差"
    return f"{tool_code} {offset_um}µm 待复核"


def apply_verdict(submission: OffsetSubmission) -> None:
    submission.verdict = evaluate_verdict(submission.offset_um)
    submission.status = OffsetSubmission.Status.DONE
    submission.reviewed_at = timezone.now()
    submission.save(
        update_fields=["verdict", "status", "reviewed_at"],
    )
