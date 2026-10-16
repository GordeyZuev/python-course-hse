import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from silent import silent


def test_silent():
    calls = []

    @silent(0)
    def give():
        calls.append(1)
        return None

    assert calls == [], "украшение не вызывает функцию"
    assert give() is None, "успех None не заменяется на default 0"
    assert calls == [1]

    @silent(0)
    def zero():
        raise ValueError("нет")

    assert zero() == 0, "ValueError отдаёт default 0"

    @silent(None)
    def nothing():
        raise RuntimeError("нет")

    assert nothing() is None, "RuntimeError отдаёт default None"

    @silent("тихо")
    def bad_type():
        raise TypeError("тип")

    assert bad_type() == "тихо", "TypeError тоже отдаёт default"

    @silent("тихо")
    def missing():
        raise KeyError("нет ключа")

    assert missing() == "тихо", "любой Exception, не только три типа, отдаёт default"

    @silent(0)
    def add(a, *, b):
        """плюс"""
        return a + b

    @silent("")
    def cat(a, b):
        return a + b

    assert add(1, b=2) == 3, "аргументы доходят"
    assert cat("а", "б") == "аб", "вторая функция со своим default"
    assert add.__name__ == "add"
    assert add.__doc__ == "плюс"
    assert cat.__name__ == "cat"

    @silent(None)
    def give_zero():
        return 0

    assert give_zero() == 0, "успех 0 не заменяется на default None"

    @silent(True)
    def give_false():
        return False

    assert give_false() is False, "успех False не заменяется на default True"

    state = {"n": 0}

    @silent("тихо")
    def maybe():
        state["n"] += 1
        if state["n"] == 1:
            raise KeyError("раз")
        return "эфир"

    assert maybe() == "тихо", "ошибка отдаёт default"
    assert maybe() == "эфир", "после ошибки функция снова работает"

    marker = ["тихо"]

    @silent(marker)
    def fail():
        raise RuntimeError("нет")

    assert fail() is marker, "наружу идёт сам объект default"
    marker.append(1)
    assert fail() == ["тихо", 1], "это тот же список, не копия"

    escaped = False
    try:
        @silent(0)
        def stop():
            raise SystemExit(1)

        stop()
    except SystemExit:
        escaped = True
    assert escaped, "SystemExit не ловится: это не Exception"

    escaped = False
    try:
        @silent(0)
        def interrupt():
            raise KeyboardInterrupt

        interrupt()
    except KeyboardInterrupt:
        escaped = True
    assert escaped, "KeyboardInterrupt не ловится: это не Exception"


if __name__ == "__main__":
    test_silent()
    print("тест silent прошёл")
