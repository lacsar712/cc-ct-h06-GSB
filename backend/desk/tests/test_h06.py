from desk.h06_extra_trap import on_detail, on_list, on_save

def test_polish_hooks():
    assert on_save("合格") in ("合格", "超差")
    assert on_list("合格") in ("合格", "超差")
    assert isinstance(on_detail("甲刀", 5, "合格"), str)

