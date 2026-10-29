import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from running import running


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

import inspect


def test_running():
    assert inspect.isgenerator(running([])), "running возвращает генератор"
    assert list(running([])) == [], "пустой источник"
    assert list(running([5])) == [5], "один элемент"
    assert list(running([1, -2, 0, 4])) == [1, -1, -1, 3], "сложение, включая нуль и минус"
    def behind(done, new):
        return done - new

    assert list(running([10, 3, 1], behind)) == [10, 7, 6], "сначала накопленное, потом новое"

    def zero(done, new):
        return 0

    assert list(running([5, 1, 2], zero)) == [5, 0, 0], "нуль в сумме не обрывает ряд"

    def source():
        yield 10
        yield 3
        raise AssertionError("третий элемент раньше второго шага")

    step = running(source())
    assert next(step) == 10, "первый шаг не тянет второй элемент"
    assert next(step) == 13, "второй шаг берёт ровно один новый элемент"


def test_stepwise_accumulation():
    calls = []
    def combine(left, right):
        calls.append((left, right))
        return left + right
    source = Source([2, 3, 4])
    result = running(source, combine)
    assert source.pulls == 0
    for budget, expected in [(1, 2), (2, 5), (3, 9)]:
        source.allowed = budget
        assert next(result) == expected
        assert source.pulls == budget
    assert calls == [(2, 3), (5, 4)], "первое значение не вызывает func; дальше один вызов на элемент"
    assert list(running([], combine)) == []
    assert list(running([0], combine)) == [0]
    assert calls == [(2, 3), (5, 4)], "для пустого источника и первого элемента func не нужна"
    assert list(running([0, 1], None)) == [0, 1]
    assert list(running(["а", "б"], lambda a, b: a + b)) == ["а", "аб"]



def test_own_implementation():
    own_iteration(running, forbid_zip=False)

if __name__ == "__main__":
    run_tests(globals())
