import functools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from partial import partial


def card(city, show, hour=0):
    return f"{city}: {show} ({hour})"


def test_partial():
    assert partial is not functools.partial, "нужна своя функция, не functools.partial"

    night = partial(card, "Москва", "ночь")
    assert not isinstance(night, functools.partial), "пресет – не объект functools.partial"
    assert night() == "Москва: ночь (0)", "только зажатые позиционные, час по умолчанию"
    assert night(3) == "Москва: ночь (3)", "новые позиционные идут после зажатых"

    assert partial(card)("Москва", "ночь", 3) == "Москва: ночь (3)", "только новые позиционные"
    assert partial(card, "Москва")("ночь", 3) == "Москва: ночь (3)", "сначала зажатые, потом новые"

    assert partial(card, "Москва", "ночь")(hour=3) == "Москва: ночь (3)", "новое имя добавляется"
    assert partial(card, "Москва", "ночь", hour=1)(hour=3) == "Москва: ночь (3)", "имя из вызова перекрывает зажатое"
    assert partial(card, hour=3)("Москва", "ночь") == "Москва: ночь (3)", "можно зажать только имя"

    moscow = partial(card, "Москва")
    kazan = partial(card, "Казань")
    assert moscow("ночь", 1) == "Москва: ночь (1)", "первый пресет"
    assert kazan("утро", 2) == "Казань: утро (2)", "второй пресет не видит первый"
    assert moscow("ночь", 1) == "Москва: ночь (1)", "первый пресет не сбился"

    calls = []

    def mute(city):
        calls.append(city)
        return None

    assert partial(mute, "Москва")() is None, "None – обычный возврат"
    assert calls == ["Москва"], "исходная функция входит один раз"

    def zero(city):
        calls.append(city)
        return 0

    assert partial(zero, "Казань")() == 0, "0 – обычный возврат"
    assert calls == ["Москва", "Казань"]

    assert partial(card)("Москва", "ночь") == "Москва: ночь (0)", "ничего не зажато"


if __name__ == "__main__":
    test_partial()
    print("тест partial прошёл")
