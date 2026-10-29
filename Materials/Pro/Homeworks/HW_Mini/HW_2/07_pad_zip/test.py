import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pad_zip import pad_zip


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


def test_pad_zip():
    assert inspect.isgenerator(pad_zip([], [])), "pad_zip возвращает генератор"
    assert list(pad_zip([], [])) == [], "обе ленты пустые"
    assert list(pad_zip([1, 2], ["a", "b"])) == [(1, "a"), (2, "b")], "равная длина"
    assert list(pad_zip([1, 2, 3], [10], fill=0)) == [(1, 10), (2, 0), (3, 0)], "левая длиннее"
    assert list(pad_zip(["a"], ["b", "c"], fill="-")) == [("a", "b"), ("-", "c")], "правая длиннее"
    assert list(pad_zip([], [1, 2])) == [(None, 1), (None, 2)], "только левая пуста"
    assert list(pad_zip([1, 2], [])) == [(1, None), (2, None)], "только правая пуста"
    assert list(pad_zip([1, 2], [10])) == [(1, 10), (2, None)], "дырка – None, в данных None нет"
    assert list(pad_zip(["Аня", "Боря"], ["1"], fill="стойка")) == [
        ("Аня", "1"),
        ("Боря", "стойка"),
    ], "гостей больше – на место стола встаёт стойка"
    assert list(pad_zip(["Аня"], ["1", "2"], fill="пусто")) == [
        ("Аня", "1"),
        ("пусто", "2"),
    ], "столов больше – на место гостя встаёт пусто"

    def left():
        yield "a"
        yield "b"

    def right():
        yield 1

    assert list(pad_zip(left(), right(), fill="-")) == [("a", 1), ("b", "-")], "стороны-генераторы"


def test_lazy_pairs_and_fill_identity():
    left, right = Source([None, 0, False]), Source([None])
    marker = []
    result = pad_zip(left, right, fill=marker)
    assert left.pulls == right.pulls == 0
    left.allowed = right.allowed = 1
    assert next(result) == (None, None), "None может быть настоящим значением"
    left.allowed = right.allowed = 2
    pair = next(result)
    assert pair[0] == 0 and pair[1] is marker
    left.allowed = right.allowed = 3
    pair = next(result)
    assert pair[0] is False and pair[1] is marker
    assert list(pad_zip(["-", "x"], ["-"], fill="-")) == [("-", "-"), ("x", "-")]
    assert list(pad_zip([None, 2], [1])) == [(None, 1), (2, None)]



def test_own_implementation():
    own_iteration(pad_zip, forbid_zip=True)


def test_left_is_read_first_and_fill_is_shared():
    events = []
    def source(name, items):
        for item in items:
            events.append(name)
            yield item
    result = pad_zip(source("left", [1, 2]), source("right", [3, 4]))
    assert next(result) == (1, 3)
    assert events == ["left", "right"], "в каждой паре сначала читается левая сторона"
    assert next(result) == (2, 4)
    assert events == ["left", "right", "left", "right"]
    marker = []
    pairs = list(pad_zip([], [1, 2], fill=marker))
    assert pairs[0][0] is marker and pairs[1][0] is marker, "слева тоже используется сам объект fill"


if __name__ == "__main__":
    run_tests(globals())
