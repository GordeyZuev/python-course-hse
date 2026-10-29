import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from take import take


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

class _Explode:
    def __iter__(self):
        return self

    def __next__(self):
        raise AssertionError("источник читали")


class _Limited:
    def __init__(self, values, allowed):
        self.values = list(values)
        self.allowed = allowed
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= self.allowed:
            raise AssertionError("лишний next")
        if self.index >= len(self.values):
            raise StopIteration
        value = self.values[self.index]
        self.index += 1
        return value


def test_take():
    assert take(0, _Explode()) == [], "n = 0 не читает источник"
    expect(lambda: take(-1, _Explode()), ValueError)
    assert take(5, []) == [], "пустой источник"
    assert take(1, [7, 8]) == [7], "ровно один элемент"
    assert take(3, [1, 2, 3]) == [1, 2, 3], "n равно длине"
    assert take(5, [1, 2]) == [1, 2], "n больше длины"
    got = take(2, (1, 2, 3))
    assert got == [1, 2], "последовательность короче не обязана быть списком на входе"
    assert isinstance(got, list), "take возвращает список"
    assert take(2, (item for item in [7, 8, 9])) == [7, 8], "генератор"
    assert take(2, _Limited([1, 2, 3, 4], 2)) == [1, 2], "третий next не случается"
    song = ["ночь"]
    assert take(1, [song])[0] is song, "элемент тот же объект, не копия"


def test_boundary_protocol():
    assert take(0, Untouched()) == []
    expect(lambda: take(-3, Untouched()), ValueError)
    source = iter([None, False, 0, "", 9])
    assert take(4, source) == [None, False, 0, ""]
    assert next(source) == 9, "хвост источника должен остаться доступным"



def test_own_implementation():
    own_iteration(take, forbid_zip=False)

if __name__ == "__main__":
    run_tests(globals())
