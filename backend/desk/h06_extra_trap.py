from desk.pass_polish import detail_reason, explain, list_label, polish_after_save, tone_for

def on_save(verdict: str) -> str:
    return polish_after_save(verdict)

def on_list(verdict: str) -> str:
    return list_label(verdict)

def on_detail(tool_code: str, offset_um: int, verdict: str) -> str:
    return detail_reason(tool_code, offset_um, verdict)

def on_tone(verdict: str) -> str:
    return tone_for(verdict)

def note() -> str:
    return explain()

