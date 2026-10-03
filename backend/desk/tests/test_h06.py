"""H06 回归：判定不得被粉饰。

真判定规则：|刀补| ≤ 12µm 判合格，否则超差。
甲刀（5µm）必须一路合格，乙刀（20µm）必须一路超差且不许被顺带改成合格；
库字段、列表话术、详情说明须与真判定同向可对拍，且不得残留粉饰钩子。
"""

import importlib.util
from pathlib import Path

import pytest
from django.utils import timezone

from desk.api import _to_out
from desk.models import OffsetSubmission
from desk.services import apply_verdict, evaluate_verdict

PASS = OffsetSubmission.Verdict.PASS  # 合格
FAIL = OffsetSubmission.Verdict.FAIL  # 超差

# 甲刀：公差内，应判合格；乙刀：超公差，应判超差
JIA = ("甲刀", 5, PASS)
YI = ("乙刀", 20, FAIL)


def make_row(tool_code, offset_um, verdict=""):
    now = timezone.now()
    return OffsetSubmission(
        id=1,
        tool_code=tool_code,
        offset_um=offset_um,
        status=OffsetSubmission.Status.DONE if verdict else OffsetSubmission.Status.PENDING,
        verdict=verdict,
        created_at=now,
        reviewed_at=now if verdict else None,
    )


def apply_in_memory(row):
    """跑真实的 apply_verdict，仅把 save 拦在内存里（本组测试不需要数据库）。"""
    saved = []
    row.save = lambda **kwargs: saved.append(kwargs)
    apply_verdict(row)
    return saved


@pytest.mark.parametrize("offset_um", [0, 1, 5, 12, -1, -12])
def test_evaluate_verdict_within_tolerance_is_pass(offset_um):
    assert evaluate_verdict(offset_um) == PASS


@pytest.mark.parametrize("offset_um", [13, 20, 100, -13, -20])
def test_evaluate_verdict_beyond_tolerance_is_fail(offset_um):
    assert evaluate_verdict(offset_um) == FAIL


@pytest.mark.parametrize("tool_code,offset_um,expected", [JIA, YI])
def test_apply_verdict_stores_true_verdict(tool_code, offset_um, expected):
    row = make_row(tool_code, offset_um)
    saved = apply_in_memory(row)
    # 库字段就是真判定：甲刀合格不被刷成超差，乙刀超差不缺位
    assert row.verdict == expected
    assert row.status == OffsetSubmission.Status.DONE
    assert row.reviewed_at is not None
    assert saved and saved[0]["update_fields"] == ["verdict", "status", "reviewed_at"]


@pytest.mark.parametrize("tool_code,offset_um,expected", [JIA, YI])
def test_list_and_detail_align_with_true_verdict(tool_code, offset_um, expected):
    row = make_row(tool_code, offset_um)
    apply_in_memory(row)
    out = _to_out(row)
    other = FAIL if expected == PASS else PASS
    # 列表结论、详情说明、库字段三者同向可对拍
    assert out.verdict == expected == row.verdict
    assert out.note == f"{tool_code} {offset_um}µm {expected}"
    assert other not in out.note


def test_jia_row_never_shows_fail_wording():
    out = _to_out(make_row(JIA[0], JIA[1], verdict=JIA[2]))
    assert out.verdict == PASS
    assert FAIL not in out.note


def test_yi_row_stays_fail_and_is_not_polished_to_pass():
    out = _to_out(make_row(YI[0], YI[1], verdict=YI[2]))
    assert out.verdict == FAIL
    assert PASS not in out.note


def test_pending_row_has_no_verdict_or_note():
    out = _to_out(make_row("T05", 3))
    assert out.verdict == ""
    assert out.note == ""


@pytest.mark.parametrize("module", ["desk.pass_polish", "desk.h06_extra_trap"])
def test_polish_hook_modules_are_gone(module):
    assert importlib.util.find_spec(module) is None


def test_no_polish_residue_in_source():
    desk_dir = Path(__file__).resolve().parents[1]
    banned = ("pass_polish", "h06_extra_trap", "polish", "POLISH", "旁路粉饰", "粉饰")
    offenders = []
    for path in desk_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if token in text:
                offenders.append(f"{path.name}: {token}")
    frontend_app = desk_dir.parents[1] / "frontend" / "src" / "App.jsx"
    if frontend_app.exists():
        if "h06-trap" in frontend_app.read_text(encoding="utf-8"):
            offenders.append("App.jsx: h06-trap")
    assert offenders == []
