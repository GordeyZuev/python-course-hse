import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chain import chain


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


def _logged(name, items, log):
    def source():
        log.append(name)
        yield from items
    return source()


def test_chain():
    syntax(chain, "yield_from")
    assert inspect.isgenerator(chain()), "chain возвращает генератор"
    assert list(chain()) == [], "вызов без источников"
    assert list(chain([1, 2])) == [1, 2], "один источник"
    assert list(chain([1], [], [2, 3])) == [1, 2, 3], "пустой источник в середине"

    def tail():
        yield 2

    assert list(chain([1], tail())) == [1, 2], "список и генератор"
    assert list(chain([1, [2, 3]], [4])) == [1, [2, 3], 4], "элемент-список не раскрывается"

    log = []
    left = _logged("left", [1, 2], log)
    right = _logged("right", [3], log)
    got = chain(left, right)
    assert log == [], "до next источники молчат"
    assert next(got) == 1
    assert log == ["left"], "второй ещё не стартовал"
    assert next(got) == 2
    assert log == ["left"]
    assert next(got) == 3
    assert log == ["left", "right"]

    log = []
    left = _logged("left", [], log)
    right = _logged("right", [3], log)
    assert next(chain(left, right)) == 3
    assert log == ["left", "right"], "пустой первый источник сразу открывает второй"


def test_no_lookahead():
    source = Source([1, 2])
    tail = Source([3])
    result = chain(source, tail)
    assert source.pulls == tail.pulls == 0
    source.allowed = 1
    assert next(result) == 1
    assert tail.pulls == 0
    source.allowed = 2
    assert next(result) == 2
    assert tail.pulls == 0
    source.allowed = 3
    tail.allowed = 1
    assert next(result) == 3
    result.close()



def test_own_implementation():
    own_iteration(chain, forbid_zip=False)

if __name__ == "__main__":
    run_tests(globals())
