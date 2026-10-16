import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shabbat import shabbat


def expect(call, error):
    try:
        call()
    except error:
        return
    except Exception as caught:
        raise AssertionError(
            f"ждали {error.__name__}, пришло {type(caught).__name__}: {caught}"
        ) from caught
    raise AssertionError(f"ждали {error.__name__}, а вызов прошёл")


def test_shabbat():
    calls = []

    @shabbat
    def say(text):
        """эфир"""
        calls.append(text)
        return text

    assert calls == [], "украшение не вызывает функцию"
    assert say("ночь") == "ночь"
    assert say("утро") == "утро"
    assert say("суббота") == "суббота"
    assert say("") == ""
    assert say("12345") == "12345"
    assert say(text="раз") == "раз", "аргумент по имени доходит, пока функция работает"
    assert say(6) == 6, "число 6 остановку не включает"
    assert say("работа") == "Отдых"
    assert say("ещё") == "Отдых"
    assert say(text="день") == "Отдых"
    assert say("      ") == "Отдых"
    assert calls == ["ночь", "утро", "суббота", "", "12345", "раз", 6, "работа"]
    assert say.__name__ == "say"
    assert say.__doc__ == "эфир"

    @shabbat
    def spaces(text):
        calls.append(text)
        return text

    before = len(calls)
    assert spaces("      ") == "Отдых", "шесть пробелов тоже строка длины 6"
    assert spaces("ночь") == "Отдых"
    assert calls[before:] == ["      "]

    @shabbat
    def give(value):
        calls.append(value)
        return value

    before = len(calls)
    assert give(6) == 6
    assert give(None) is None
    assert give(False) is False
    assert give(["а", "б", "в", "г", "д", "е"]) == ["а", "б", "в", "г", "д", "е"]
    assert give(b"123456") == b"123456"
    assert give("раз") == "раз"
    assert give("работа") == "Отдых"
    assert give("ещё") == "Отдых"
    assert calls[before:] == [
        6,
        None,
        False,
        ["а", "б", "в", "г", "д", "е"],
        b"123456",
        "раз",
        "работа",
    ]

    @shabbat
    def join(left, right):
        return left + right

    assert join("а", "б") == "аб"
    assert join("аб", "вгде") == "Отдых"
    assert join("а", "б") == "Отдых"

    @shabbat
    def boom(kind):
        calls.append(kind)
        if kind == "тип":
            raise TypeError("тип")
        if kind == "ошибка":
            raise ValueError("нет")
        return kind

    before = len(calls)
    expect(lambda: boom("тип"), TypeError)
    expect(lambda: boom("ошибка"), ValueError)
    assert boom("раз") == "раз", "ошибка остановку не включает"
    assert boom("работа") == "Отдых"
    assert boom("ошибка") == "Отдых", "после остановки упавший вызов в тело не входит"
    assert calls[before:] == ["тип", "ошибка", "раз", "работа"]

    @shabbat
    def other():
        return "ночь"

    assert say("два") == "Отдых", "первая функция так и стоит"
    assert other() == "ночь"
    assert other() == "ночь"


if __name__ == "__main__":
    test_shabbat()
    print("тест shabbat прошёл")
