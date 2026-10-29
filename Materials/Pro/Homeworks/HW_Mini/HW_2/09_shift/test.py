import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shift import shift


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


def test_shift():
    syntax(shift, "finally")
    log = []
    orders = shift(["латте", "чай"], log)
    assert inspect.isgenerator(orders), "shift возвращает генератор"
    assert next(orders) == "латте"
    assert log == [], "смена ещё не закрыта"
    assert list(orders) == ["чай"], "хвост заказов на месте"
    assert log == ["закрыта"], "после нормального конца смена закрыта один раз"
    orders.close()
    assert log == ["закрыта"], "повторный close не пишет отметку второй раз"

    empty = []
    assert list(shift([], empty)) == [], "пустой ряд"
    assert empty == ["закрыта"], "пустая смена тоже закрывается"

    lost = []
    broken = shift(["латте", "чай"], lost)
    assert next(broken) == "латте"
    expect(lambda: broken.throw(ValueError("нет")), ValueError)
    assert lost == ["закрыта"], "ошибка вышла наружу, смена закрыта"
    expect(lambda: next(broken), StopIteration)

    typed = []
    other = shift(["латте"], typed)
    assert next(other) == "латте"
    expect(lambda: other.throw(TypeError("тип")), TypeError)
    assert typed == ["закрыта"], "TypeError тоже закрывает смену"

    mid = []
    live = shift(["латте", "чай", "какао"], mid)
    assert next(live) == "латте"
    live.close()
    assert mid == ["закрыта"], "close закрывает смену"
    expect(lambda: next(live), StopIteration)

    left_log = []
    right_log = []
    left = shift(["а"], left_log)
    right = shift(["б"], right_log)
    assert list(left) == ["а"]
    assert left_log == ["закрыта"]
    assert right_log == [], "чужая смена ещё открыта"
    assert list(right) == ["б"]
    assert right_log == ["закрыта"]



def test_lifecycle_boundaries():
    log = ["прошлая смена"]
    untouched = shift(Untouched(), log)
    untouched.close()
    assert log == ["прошлая смена"], "незапущенная смена не пишет отметку"
    source = Source(["латте"], allowed=1)
    orders = shift(source, log)
    assert source.pulls == 0
    assert next(orders) == "латте"
    assert log == ["прошлая смена"], "выдача последнего заказа ещё не завершила генератор"
    orders.close()
    orders.close()
    assert log == ["прошлая смена", "закрыта"]
    def broken_source():
        yield "латте"
        raise RuntimeError("источник")
    log = []
    orders = shift(broken_source(), log)
    next(orders)
    expect(lambda: next(orders), RuntimeError)
    assert log == ["закрыта"]



def test_own_implementation():
    own_iteration(shift, forbid_zip=False)

if __name__ == "__main__":
    run_tests(globals())
