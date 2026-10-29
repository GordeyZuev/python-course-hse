import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from group_runs import group_runs


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


def test_group_runs():
    assert inspect.isgenerator(group_runs([])), "group_runs возвращает генератор"
    assert list(group_runs([])) == [], "пустой источник"
    assert list(group_runs([1])) == [[1]], "один элемент"
    assert list(group_runs([1, 2, 3])) == [[1], [2], [3]], "все разные"
    assert list(group_runs([1, 1, 1])) == [[1, 1, 1]], "все одинаковые"
    assert list(group_runs([1, 2, 2, 3])) == [[1], [2, 2], [3]], "серия длины 1 с краю"
    assert list(group_runs([1, 2, 1])) == [[1], [2], [1]], "одинаковые врозь не склеиваются"
    groups = list(group_runs([1, True, 2]))
    assert len(groups) == 2, "после серии 1/True идёт отдельная двойка"
    assert groups[0][0] == 1 and groups[0][1] is True, "1 и True – одна серия, True остаётся True"
    assert groups[1] == [2]
    assert list(group_runs(["a", "a", "b"])) == [["a", "a"], ["b"]], "строки"

    def tracks():
        yield "a"
        yield "a"
        yield "b"

    assert list(group_runs(tracks())) == [["a", "a"], ["b"]], "одноразовый генератор"


def test_series_lookahead_and_objects():
    a, b, c = [1], [1], [2]
    source = Source([a, b, c, None, None, 0, False, ""])
    result = group_runs(source)
    assert source.pulls == 0
    source.allowed = 3
    first = next(result)
    assert len(first) == 2 and first[0] is a and first[1] is b
    source.allowed = 4
    assert next(result)[0] is c
    assert len(first) == 2 and first[0] is a, "выданная серия больше не меняется"
    source.allowed = 9
    assert list(result) == [[None, None], [0, False], [""]]



def test_own_implementation():
    own_iteration(group_runs, forbid_zip=False)

if __name__ == "__main__":
    run_tests(globals())
