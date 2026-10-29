import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from replay import replay


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


def test_replay():
    pulled = []

    def bomb():
        pulled.append(1)
        yield 1

    expect(lambda: list(replay(bomb(), -1)), ValueError)
    assert pulled == [], "отрицательный times не читает источник"

    idle = replay(bomb(), 0)
    assert inspect.isgenerator(idle), "times = 0 всё равно генератор"
    assert list(idle) == [], "times = 0 пусто"
    assert pulled == [], "times = 0 не читает источник"

    def tape():
        yield "ля"
        yield "си"

    assert list(replay(tape(), 1)) == ["ля", "си"], "один круг без повтора"
    once = tape()
    assert list(replay(once, 2)) == ["ля", "си", "ля", "си"], "два круга с одноразовой плёнки"
    assert list(once) == [], "исходная плёнка после прохода пуста"

    def short():
        yield "a"
        yield "b"

    assert list(replay(short(), 3)) == ["a", "b", "a", "b", "a", "b"], "три круга"
    assert list(replay(iter(()), 5)) == [], "пустой источник"
    assert list(replay(["б", "а"], 2)) == ["б", "а", "б", "а"], "порядок сохраняется"


def test_cache_timing_and_identity():
    invalid = replay(Untouched(), -1)
    assert inspect.isgenerator(invalid), "ошибка возникает при обходе, а не при создании генератора"
    expect(lambda: next(invalid), ValueError)
    assert list(replay(Untouched(), 0)) == []
    marker = []
    source = Source([marker, None], allowed=3)
    result = replay(source, 2)
    assert inspect.isgenerator(result)
    assert source.pulls == 0
    assert next(result) is marker
    assert source.pulls == 3, "перед первым результатом конечный источник полностью сохранён"
    assert next(result) is None
    assert next(result) is marker
    assert next(result) is None
    expect(lambda: next(result), StopIteration)
    assert source.pulls == 3, "повтор читает сохранённые элементы"



def test_own_implementation():
    own_iteration(replay, forbid_zip=False)


def test_input_list_stays_unchanged():
    marker = []
    items = [marker, "конец"]
    output = list(replay(items, 2))
    assert len(items) == 2 and items[0] is marker and items[1] == "конец", "входной список не меняется"
    assert output[0] is marker and output[2] is marker


if __name__ == "__main__":
    run_tests(globals())
