import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tune as radio
from tune import listen, tune


def test_tune():
    radio.FREQ = 100
    assert listen() == 100, "старт из модуля"
    assert radio.FREQ == 100, "listen не меняет частоту"

    assert tune(5) == 105
    assert listen() == 105, "listen видит запись tune"
    assert radio.FREQ == 105

    assert tune(0) == 105, "нулевая дельта"
    assert tune(-3) == 102
    assert listen() == 102

    radio.FREQ = 90
    assert listen() == 90, "снаружи записали в имя модуля"
    assert tune(-3) == 87, "tune прибавляет к тому, что лежит сейчас"
    assert radio.FREQ == 87
    assert listen() == 87

    radio.FREQ = 4
    assert tune(-4) == 0, "частота может стать нулём"
    assert radio.FREQ == 0
    assert listen() == 0, "ноль остаётся нулём"

    radio.FREQ = 0
    assert tune(-5) == -5, "ниже нуля можно"
    assert listen() == -5

    radio.FREQ = 100


if __name__ == "__main__":
    test_tune()
    print("тест tune прошёл")
