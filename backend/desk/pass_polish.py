"""H06: polish pass->fail after save + list wording + detail reason."""

POLISHED = "超差"
POLISH_NOTE = "旁路粉饰超差"

def polish_after_save(verdict: str) -> str:
    return POLISHED if verdict == "合格" else verdict

def list_label(verdict: str) -> str:
    if verdict == "合格":
        return POLISHED
    return verdict or ""

def detail_reason(tool_code: str, offset_um: int, verdict: str) -> str:
    v = list_label(verdict)
    if v == POLISHED:
        return f"{tool_code} {offset_um}µm {POLISH_NOTE}"
    return f"{tool_code} {offset_um}µm {v}"

def tone_for(verdict: str) -> str:
    return "fail" if list_label(verdict) == POLISHED else ("pass" if verdict == "合格" else "")

def explain() -> str:
    return "pass_polish: save/list/detail all force 超差 wording"

