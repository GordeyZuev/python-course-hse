import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from counted import counted


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

def test_counted():
    calls = []

    @counted
    def ready():
        calls.append(1)
        return "готово"

    assert calls == [], "украшение не вызывает функцию"
    assert ready.calls == 0, "до вызова счётчик ноль"
    assert ready() == "готово"
    assert ready.calls == 1, "успех прибавляет один"
    assert ready() == "готово"
    assert ready.calls == 2, "второй успех"

    @counted
    def boom():
        raise ValueError("сломалось")

    caught = None
    try:
        boom()
    except ValueError as error:
        caught = error
    assert caught is not None and str(caught) == "сломалось", "исключение летит дальше с тем же текстом"
    assert boom.calls == 1, "исключение тоже считается"

    @counted
    def mix(a, b, *, c):
        """сводка"""
        return (a, b, c)

    assert mix(1, 2, c=3) == (1, 2, 3), "аргументы доходят до тела"
    assert mix.__name__ == "mix", "имя исходной функции"
    assert mix.__doc__ == "сводка", "документация исходной функции"

    @counted
    def left():
        return 1

    @counted
    def right():
        return 2

    left()
    assert left.calls == 1
    assert right.calls == 0, "у второй функции свой счётчик"

if __name__ == "__main__":
    test_counted()
    print("тест counted прошёл")
