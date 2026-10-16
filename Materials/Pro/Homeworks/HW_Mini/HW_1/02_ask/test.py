import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ask import ask


def test_ask():
    assert ask() == "не передали", "вызов без аргумента"
    assert ask(None) is None, "None – переданный ответ"
    assert ask() == "не передали", "прошлый None не становится пропуском"
    assert ask(0) == 0, "ноль – ответ"
    assert ask(False) is False, "False – ответ"
    assert ask("") == "", "пустая строка – ответ"
    assert ask("Аня") == "Аня"

    box = ["кабель"]
    assert ask(box) is box, "переданный объект возвращается как есть"
    assert ask() == "не передали"


if __name__ == "__main__":
    test_ask()
    print("тест ask прошёл")
