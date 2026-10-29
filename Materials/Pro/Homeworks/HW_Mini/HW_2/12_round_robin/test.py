import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from round_robin import round_robin


import inspect


def test_round_robin():
    assert inspect.isgenerator(round_robin()), "round_robin возвращает генератор"
    assert list(round_robin()) == [], "вызов без рядов"
    assert list(round_robin([])) == [], "один пустой ряд"
    assert list(round_robin(["а", "б"])) == ["а", "б"], "один ряд идёт по порядку"
    assert list(round_robin(["а1", "а2"], ["б1", "б2"])) == [
        "а1",
        "б1",
        "а2",
        "б2",
    ], "равные ряды чередуются"
    assert list(round_robin(["а1", "а2", "а3"], ["б1"])) == [
        "а1",
        "б1",
        "а2",
        "а3",
    ], "после конца второго остаётся только первый"
    assert list(round_robin(["а"], ["б1", "б2", "б3"])) == [
        "а",
        "б1",
        "б2",
        "б3",
    ], "после конца первого остаётся только второй"
    assert list(round_robin(["а"], [], ["в"])) == ["а", "в"], "пустой ряд выпадает"
    assert list(round_robin([], [], [])) == [], "все ряды пустые"
    assert list(round_robin([1, [2, 3]], [4])) == [1, 4, [2, 3]], "элемент-список не раскрывается"

    started = []

    def row(name, items):
        started.append(name)
        yield from items

    left = row("левый", ["а1", "а2"])
    right = row("правый", ["б1"])
    got = round_robin(left, right)
    assert started == [], "до next ряды не читаются"
    assert next(got) == "а1"
    assert started == ["левый"], "второй ряд ещё не начат"
    assert next(got) == "б1"
    assert started == ["левый", "правый"]
    assert next(got) == "а2", "после конца правого берём только левый"



def test_three_live_sources_and_each_step():
    sources = [Source(["a1", "a2", "a3"]), Source(["b1"]), Source(["c1", "c2"])]
    result = round_robin(*sources)
    assert all(s.pulls == 0 for s in sources)
    for budgets, expected in [((1, 0, 0), "a1"), ((1, 1, 0), "b1"), ((1, 1, 1), "c1"),
                              ((2, 1, 1), "a2"), ((2, 2, 2), "c2"), ((3, 2, 2), "a3")]:
        for source, budget in zip(sources, budgets):
            source.allowed = budget
        assert next(result) == expected, "очередь не должна пропустить соседа выбывшего источника"
    result.close()
    assert list(round_robin([], [1], [], [2, 3], [])) == [1, 2, 3]



def test_own_implementation():
    own_iteration(round_robin, forbid_zip=False)


def test_original_objects_and_exhaustion():
    left, right = [], []
    output = list(round_robin([left, None], [right, False, 0]))
    assert output[0] is left and output[1] is right, "элементы не копируются"
    assert output[2] is None and output[3] is False and output[4] == 0
    sources = [Source([1], allowed=2), Source([2, 3, 4], allowed=4)]
    assert list(round_robin(*sources)) == [1, 2, 3, 4]
    assert sources[0].pulls == 2, "исчерпанный источник больше не опрашивается"


if __name__ == "__main__":
    run_tests(globals())
