"""修复曾被粉饰钩子改写的库字段：按公差规则重算已有结论。

只纠正与真判定不一致的行；真实超差（|offset| > 12µm）的记录保持超差，
不会被顺带改成合格。
"""

from django.conf import settings
from django.db import migrations
from django.db.models import Q

PASS = "合格"
FAIL = "超差"


def recompute_verdicts(apps, schema_editor):
    OffsetSubmission = apps.get_model("desk", "OffsetSubmission")
    tolerance = getattr(settings, "OFFSET_TOLERANCE_UM", 12)
    judged = OffsetSubmission.objects.exclude(verdict="")
    within = Q(offset_um__lte=tolerance) & Q(offset_um__gte=-tolerance)
    judged.filter(within).exclude(verdict=PASS).update(verdict=PASS)
    judged.exclude(within).exclude(verdict=FAIL).update(verdict=FAIL)


class Migration(migrations.Migration):
    dependencies = [("desk", "0001_initial")]

    operations = [
        migrations.RunPython(recompute_verdicts, migrations.RunPython.noop),
    ]
