import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from calls import calls


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


def test_calls():
    syntax(calls, "value_error")
    assert inspect.isgenerator(calls([])), "calls возвращает генератор"
    assert list(calls([])) == [], "пустой ряд"
    assert list(calls(["латте"])) == ["латте"], "ошибки не было – заказ как есть"

    orders = calls(["латте", "капучино", "чай"])
    assert next(orders) == "латте", "первый заказ"
    assert orders.throw(ValueError("нет сиропа")) == "вода", "ValueError заменяется на воду"
    assert next(orders) == "капучино", "после замены идёт следующий заказ"
    assert orders.throw(ValueError("нет молока")) == "вода", "вторая замена"
    assert next(orders) == "чай", "ряд продолжается"

    last = calls(["латте"])
    assert next(last) == "латте"
    assert last.throw(ValueError("нет")) == "вода", "замена на последнем заказе"
    expect(lambda: next(last), StopIteration)

    broken = calls(["латте", "чай"])
    assert next(broken) == "латте"
    expect(lambda: broken.throw(TypeError("тип")), TypeError)
    expect(lambda: next(broken), StopIteration)

    pulled = []

    def source():
        yield "латте"
        pulled.append("капучино")
        yield "капучино"

    lazy = calls(source())
    assert pulled == [], "до next ряд не читается"
    assert next(lazy) == "латте"
    assert pulled == [], "следующий заказ не читается заранее"
    assert lazy.throw(ValueError("нет")) == "вода"
    assert next(lazy) == "капучино"
    assert pulled == ["капучино"]

    left = calls(["а"])
    right = calls(["б"])
    assert next(left) == "а"
    assert left.throw(ValueError("нет")) == "вода"
    assert next(right) == "б", "вторая очередь не видит чужую замену"



def test_errors_at_different_pauses():
    orders = calls(["латте", "чай"])
    next(orders)
    assert orders.throw(ValueError("нет")) == "вода"
    expect(lambda: orders.throw(ValueError("снова")), ValueError)
    expect(lambda: next(orders), StopIteration)
    def broken_source():
        yield "латте"
        raise ValueError("источник сломан")
    orders = calls(broken_source())
    assert next(orders) == "латте"
    expect(lambda: next(orders), ValueError)
    expect(lambda: next(orders), StopIteration)
    source = Source(["латте", "чай"], allowed=1)
    orders = calls(source)
    next(orders)
    assert orders.throw(ValueError()) == "вода"
    assert source.pulls == 1, "замена не забирает следующий заказ"
    orders.close()



def test_own_implementation():
    own_iteration(calls, forbid_zip=False)

def test_only_value_error_is_handled():
    for error_type in (TypeError, KeyError, RuntimeError, SystemExit, KeyboardInterrupt):
        orders = calls(["латте", "чай"])
        next(orders)
        expect(lambda: orders.throw(error_type("остановка")), error_type)
        expect(lambda: next(orders), StopIteration)


if __name__ == "__main__":
    run_tests(globals())
