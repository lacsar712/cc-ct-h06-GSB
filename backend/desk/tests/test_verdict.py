"""H06 回归：判定、库字段、列表话术、详情说明必须与真判定同向，对拍一致。

两类场景都要验：
- 甲刀：刀补 5µm（≤ 12µm 公差）→ 合格，绝不能被刷成超差；
- 乙刀：刀补 20µm（> 12µm 公差）→ 超差，不许被"顺带修好"成合格。
"""

import importlib.util

from django.test import TestCase

from desk.models import OffsetSubmission, User
from desk.services import apply_verdict, evaluate_verdict, verdict_reason

TOLERANCE = 12


class EvaluateVerdictTests(TestCase):
    def test_jia_tool_within_tolerance_is_pass(self):
        # 甲刀 5µm：合格
        self.assertEqual(evaluate_verdict(5), OffsetSubmission.Verdict.PASS)
        self.assertEqual(evaluate_verdict(-5), OffsetSubmission.Verdict.PASS)

    def test_boundary_is_pass(self):
        self.assertEqual(evaluate_verdict(TOLERANCE), OffsetSubmission.Verdict.PASS)
        self.assertEqual(evaluate_verdict(-TOLERANCE), OffsetSubmission.Verdict.PASS)

    def test_yi_tool_out_of_tolerance_is_fail(self):
        # 乙刀 20µm：超差
        self.assertEqual(evaluate_verdict(20), OffsetSubmission.Verdict.FAIL)
        self.assertEqual(evaluate_verdict(-13), OffsetSubmission.Verdict.FAIL)


class PersistVerdictTests(TestCase):
    def _apply(self, tool_code: str, offset_um: int) -> OffsetSubmission:
        user = User.objects.create(username=f"u_{offset_um}", role=User.Role.MACHINIST)
        row = OffsetSubmission.objects.create(
            tool_code=tool_code,
            offset_um=offset_um,
            submitted_by=user,
            status=OffsetSubmission.Status.PENDING,
        )
        apply_verdict(row)
        row.refresh_from_db()
        return row

    def test_jia_pass_persisted_as_pass_not_rewritten(self):
        row = self._apply("甲刀", 5)
        self.assertEqual(row.verdict, OffsetSubmission.Verdict.PASS)
        self.assertEqual(row.status, OffsetSubmission.Status.DONE)
        self.assertIsNotNone(row.reviewed_at)

    def test_yi_fail_persisted_as_fail(self):
        row = self._apply("乙刀", 20)
        self.assertEqual(row.verdict, OffsetSubmission.Verdict.FAIL)
        self.assertEqual(row.status, OffsetSubmission.Status.DONE)


class ReasonWordingTests(TestCase):
    def test_pass_reason_agrees_with_verdict(self):
        reason = verdict_reason("甲刀", 5, OffsetSubmission.Verdict.PASS)
        self.assertIn("合格", reason)
        self.assertNotIn("超差", reason)
        self.assertNotIn("粉饰", reason)

    def test_fail_reason_agrees_with_verdict(self):
        reason = verdict_reason("乙刀", 20, OffsetSubmission.Verdict.FAIL)
        self.assertIn("超差", reason)
        self.assertNotIn("合格", reason)
        self.assertNotIn("粉饰", reason)


class ApiParityTests(TestCase):
    """接口返回值（列表/详情）与库内真判定对拍，话术、色块依据同向。"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="auditor_check",
            password="x",
            role=User.Role.AUDITOR,
        )
        cls.jia = OffsetSubmission.objects.create(
            tool_code="甲刀",
            offset_um=5,
            submitted_by=cls.user,
            status=OffsetSubmission.Status.DONE,
            verdict=OffsetSubmission.Verdict.PASS,
        )
        cls.yi = OffsetSubmission.objects.create(
            tool_code="乙刀",
            offset_um=20,
            submitted_by=cls.user,
            status=OffsetSubmission.Status.DONE,
            verdict=OffsetSubmission.Verdict.FAIL,
        )

    def _get(self, path: str):
        from datetime import datetime, timedelta, timezone

        from jose import jwt

        token = jwt.encode(
            {
                "sub": str(self.user.pk),
                "username": self.user.username,
                "role": self.user.role,
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            "cnc-offset-desk-dev-secret-change-me",
            algorithm="HS256",
        )
        from ninja.testing import TestClient

        from desk.api import api

        client = TestClient(api)
        resp = client.get(path, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200, resp.content)
        return resp.json()

    def test_list_matches_db_for_both_cases(self):
        data = {r["id"]: r for r in self._get("/submissions")}

        jia = data[self.jia.id]
        self.assertEqual(jia["verdict"], "合格")
        self.assertIn("合格", jia["note"])
        self.assertNotIn("超差", jia["note"])
        self.assertNotIn("粉饰", jia["note"])

        yi = data[self.yi.id]
        self.assertEqual(yi["verdict"], "超差")
        self.assertIn("超差", yi["note"])
        self.assertNotIn("合格", yi["note"])
        self.assertNotIn("粉饰", yi["note"])

    def test_detail_matches_db_for_both_cases(self):
        jia = self._get(f"/submissions/{self.jia.id}")
        self.assertEqual(jia["verdict"], "合格")
        self.assertIn("合格", jia["note"])
        self.assertNotIn("超差", jia["note"])

        yi = self._get(f"/submissions/{self.yi.id}")
        self.assertEqual(yi["verdict"], "超差")
        self.assertIn("超差", yi["note"])
        self.assertNotIn("合格", yi["note"])


class TrapRemovalTests(TestCase):
    """粉饰钩子模块必须彻底删除，不得留下半截粉饰痕迹。"""

    def test_polish_modules_gone(self):
        self.assertIsNone(importlib.util.find_spec("desk.h06_extra_trap"))
        self.assertIsNone(importlib.util.find_spec("desk.pass_polish"))
