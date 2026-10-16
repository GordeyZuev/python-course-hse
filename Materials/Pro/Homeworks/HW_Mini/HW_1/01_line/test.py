import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from line import line


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


def test_line():
    assert line("ночь") == "ночь", "только название"
    assert line("") == "", "пустое название без артистов"
    assert line("ночь", "Аня") == "ночь - Аня", "один артист"
    assert line("ночь", "Аня", "Боря") == "ночь - Аня, Боря", "порядок артистов"
    assert line("ночь", "Аня", "Боря", "Вера") == "ночь - Аня, Боря, Вера", "три артиста"
    assert line("ночь", "Аня", year=2000) == "ночь - Аня (2000)", "год в конце"
    assert line("ночь", "Аня", "Боря", year=2000) == "ночь - Аня, Боря (2000)", "артисты и год вместе"
    assert line("ночь", year=0) == "ночь (0)", "ноль – это год, не пустота"
    assert line("ночь", year=None) == "ночь", "явный year=None как пропущенный год"
    assert line("ночь", "") == "ночь - ", "пустой артист остаётся в строке"
    assert line("Кида", "Радиохэд", year=0) == "Кида - Радиохэд (0)", "кириллица"
    expect(lambda: line(title="ночь"), TypeError)


if __name__ == "__main__":
    test_line()
    print("тест line прошёл")
