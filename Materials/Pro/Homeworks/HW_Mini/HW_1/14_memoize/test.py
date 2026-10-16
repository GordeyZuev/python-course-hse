import functools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from memoize import memoize


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


def test_memoize():
    assert memoize is not functools.lru_cache

    calls = []

    @memoize
    def fib(n):
        """числа"""
        calls.append(n)
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)

    assert calls == [], "украшение не вызывает функцию"
    assert fib(10) == 55
    assert fib(0) == 0
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(5) == 5
    assert sorted(calls) == list(range(11)), "каждое n от 0 до 10 посчитано один раз"
    assert len(calls) == 11
    assert calls.count(0) == 1, "ноль тоже лежит в словаре"

    assert fib(10) == 55
    assert fib(0) == 0
    assert len(calls) == 11, "повтор не считает заново"
    assert fib.__name__ == "fib"
    assert fib.__doc__ == "числа"

    before = len(calls)
    expect(lambda: fib(n=4), TypeError)
    assert len(calls) == before, "именованный аргумент не входит в тело"

    state = {"n": 0}

    @memoize
    def flaky(x):
        state["n"] += 1
        if state["n"] == 1:
            raise ValueError("первый")
        return x

    expect(lambda: flaky(5), ValueError)
    assert flaky(5) == 5, "после исключения тот же вызов входит снова"
    assert state["n"] == 2
    assert flaky(5) == 5
    assert state["n"] == 2, "успех уже лежит в словаре"

    @memoize
    def other(n):
        return n + 1

    assert other(10) == 11, "у второй функции свой словарь"
    assert fib(10) == 55

    seen = []

    @memoize
    def diff(a, b):
        seen.append((a, b))
        return a - b

    assert diff(1, 2) == -1
    assert diff(1, 9) == -8, "тот же первый аргумент и другой второй – другой ключ"
    assert diff(2, 1) == 1, "порядок аргументов входит в ключ"
    assert diff(1, 2) == -1
    assert seen == [(1, 2), (1, 9), (2, 1)], "повтор пары тело не вызывает"


if __name__ == "__main__":
    test_memoize()
    print("тест memoize прошёл")
