import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unpack import unpack


def test_unpack():
    assert unpack([]) == [], "пустая коробка"
    assert unpack(["книга", "мяч"]) == ["книга", "мяч"], "порядок плоского ряда"
    assert unpack([""]) == [""], "пустая строка остаётся подарком"
    assert unpack(["", "мяч"]) == ["", "мяч"], "пустая строка не выкидывается"
    assert unpack([[], "мяч", [[]]]) == ["мяч"], "пустые коробки исчезают"
    assert unpack(["мяч", ["кубик", ["конфеты"]], "книга"]) == [
        "мяч",
        "кубик",
        "конфеты",
        "книга",
    ], "три уровня"
    assert unpack(["аб", ["кубик"]]) == ["аб", "кубик"], "строка не разбирается на буквы"
    assert unpack([[["бант"]]]) == ["бант"], "коробка в коробке"


if __name__ == "__main__":
    test_unpack()
    print("тест unpack прошёл")
