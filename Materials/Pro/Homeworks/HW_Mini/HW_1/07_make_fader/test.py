import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_fader import make_fader


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

def test_fader():
    change = make_fader(40)
    assert change(0) == 40, "нулевой шаг оставляет старт"

    change = make_fader(20)
    assert change(10) == 30, "шаг прибавляется"
    assert change(15) == 45, "следующий шаг идёт от нового уровня"

    change = make_fader(90)
    assert change(20) == 100, "выше 100 не подняться"
    assert change(5) == 100, "лишнее за упором не копится"
    assert change(-5) == 95, "после упора шаг идёт от 100"

    change = make_fader(10)
    assert change(-40) == 0, "ниже 0 не опуститься"
    assert change(-3) == 0, "лишнее ниже нуля не копится"
    assert change(4) == 4, "после упора шаг идёт от 0"

    assert make_fader(8)(-8) == 0, "ровно 0 достижим"
    assert make_fader(80)(20) == 100, "ровно 100 достижим"
    assert make_fader(0)(0) == 0, "старт 0"
    assert make_fader(100)(0) == 100, "старт 100"

    left = make_fader(10)
    right = make_fader(50)
    assert left(5) == 15
    assert right(0) == 50, "второй фейдер не видит первый"
    assert left(0) == 15, "первый фейдер помнит свой уровень"

if __name__ == "__main__":
    test_fader()
    print("тест make_fader прошёл")
