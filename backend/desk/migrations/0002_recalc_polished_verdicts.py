from django.conf import settings
from django.db import migrations


def recalc_verdicts(apps, schema_editor):
    """按真实公差回填曾被粉饰钩子刷错的存量判定。

    |offset_um| <= OFFSET_TOLERANCE_UM -> 合格，否则 -> 超差。
    仅修正已有结论（verdict 非空）的记录，待复核记录不动。
    """
    OffsetSubmission = apps.get_model("desk", "OffsetSubmission")
    tolerance = settings.OFFSET_TOLERANCE_UM
    for row in OffsetSubmission.objects.exclude(verdict=""):
        true_verdict = "合格" if abs(row.offset_um) <= tolerance else "超差"
        if row.verdict != true_verdict:
            row.verdict = true_verdict
            row.save(update_fields=["verdict"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("desk", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(recalc_verdicts, reverse_code=noop),
    ]
