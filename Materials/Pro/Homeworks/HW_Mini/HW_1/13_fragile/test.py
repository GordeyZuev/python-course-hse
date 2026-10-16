import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fragile import fragile


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


def test_fragile():
    calls = []

    @fragile(0)
    def dead(text):
        calls.append(text)
        return text

    assert calls == [], "украшение не вызывает функцию"
    assert dead("ночь") == "Функция сломана", "n = 0 сразу отдаёт фразу"
    assert calls == [], "n = 0 не пускает в тело"

    calls = []

    @fragile(2)
    def twice(kind):
        calls.append(kind)
        if kind == "пробой":
            raise ValueError("пробой")
        return kind

    assert twice("ночь") == "ночь", "успех не тратит жизнь"
    caught = None
    try:
        twice("пробой")
    except ValueError as error:
        caught = error
    assert caught is not None and str(caught) == "пробой", "первая из двух ошибок выходит как есть"
    caught = None
    try:
        twice("пробой")
    except ValueError as error:
        caught = error
    assert caught is not None and str(caught) == "пробой", "вторая ошибка тоже выходит как есть"
    assert twice("утро") == "Функция сломана", "после двух падений следующий вызов – фраза"
    assert calls == ["ночь", "пробой", "пробой"], "после двух жизней тело не входит"

    calls = []

    @fragile(4)
    def take(kind):
        calls.append(kind)
        if kind == "пробой":
            raise ValueError("пробой")
        if kind == "тип":
            raise TypeError("тип")
        if kind == "дуга":
            raise RuntimeError("дуга")
        if kind == "чужая":
            raise KeyError("чужая")
        return kind

    assert take("ночь") == "ночь", "успех возвращает результат и не тратит жизнь"
    caught = None
    try:
        take("пробой")
    except ValueError as error:
        caught = error
    assert caught is not None and str(caught) == "пробой", "первое падение летит как есть"
    assert take("утро") == "утро", "успех между падениями не тратит жизнь"
    caught = None
    try:
        take("тип")
    except TypeError as error:
        caught = error
    assert caught is not None and str(caught) == "тип", "TypeError тоже тратит жизнь и летит как есть"
    caught = None
    try:
        take("дуга")
    except RuntimeError as error:
        caught = error
    assert caught is not None and str(caught) == "дуга", "RuntimeError летит со своим текстом"
    caught = None
    try:
        take("пробой")
    except ValueError as error:
        caught = error
    assert str(caught) == "пробой", "четвёртое падение ещё настоящее"
    assert calls == ["ночь", "пробой", "утро", "тип", "дуга", "пробой"]
    assert take("день") == "Функция сломана", "после четырёх падений тело не стартует"
    assert take("ночь") == "Функция сломана", "сломанная функция отвечает фразой и на удачный вызов"
    assert calls == ["ночь", "пробой", "утро", "тип", "дуга", "пробой"], "после запаса тело молчит"

    calls = []

    @fragile(1)
    def mixed(kind):
        calls.append(kind)
        if kind == "чужая":
            raise KeyError("чужая")
        if kind == "пробой":
            raise ValueError("пробой")
        return kind

    expect(lambda: mixed("чужая"), KeyError)
    assert calls == ["чужая"], "чужая ошибка входит в тело"
    assert mixed("ночь") == "ночь", "KeyError жизнь не тратит"
    expect(lambda: mixed("пробой"), ValueError)
    assert mixed("день") == "Функция сломана", "после единственной жизни функция сломана"
    assert calls == ["чужая", "ночь", "пробой"]

    @fragile(1)
    def left():
        """левый"""
        raise ValueError("л")

    @fragile(1)
    def right(text, *, extra):
        """правый"""
        return text + extra

    expect(left, ValueError)
    assert left() == "Функция сломана"
    assert right("ночь", extra="!") == "ночь!", "аргументы доходят"
    assert right("ночь", extra="!") == "ночь!", "живой запас не видит чужой"
    assert left.__name__ == "left"
    assert left.__doc__ == "левый"
    assert right.__name__ == "right"
    assert right.__doc__ == "правый"


if __name__ == "__main__":
    test_fragile()
    print("тест fragile прошёл")
