import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vandal import vandal


def test_vandal():
    calls = []

    @vandal
    def say(text):
        """эфир"""
        calls.append(text)
        return text

    assert calls == [], "украшение не вызывает функцию"
    assert say.__doc__ == "рифэ", "кириллица переворачивается"
    assert say.__name__ == "say", "имя исходной функции"
    assert say("ночь") == "ночь", "позиционный аргумент и результат"
    assert say(text="утро") == "утро", "именованный аргумент"

    @vandal
    def note():
        "а б\n"
        return "ок"

    assert note.__doc__ == "\nб а", "пробел и перевод строки остаются символами"

    @vandal
    def quiet():
        return "тихо"

    assert quiet.__doc__ is None, "нет docstring – снаружи None"

    @vandal
    def blank():
        """"""
        return ""

    assert blank.__doc__ == "", "пустая строка остаётся пустой"

    @vandal
    def give(value):
        return value

    assert give(None) is None, "None – обычный возврат"
    assert give(0) == 0, "0 – обычный возврат"

    @vandal
    def boom():
        calls.append("бум")
        raise ValueError("сломалось")

    caught = None
    try:
        boom()
    except ValueError as error:
        caught = error
    assert caught is not None and str(caught) == "сломалось", "исключение летит дальше с тем же текстом"

    @vandal
    def left():
        """лево"""
        return 1

    @vandal
    def right():
        """право"""
        return 2

    assert left.__doc__ == "овел"
    assert right.__doc__ == "оварп", "у второй функции свой docstring"
    assert left.__doc__ == "овел"


if __name__ == "__main__":
    test_vandal()
    print("тест vandal прошёл")
