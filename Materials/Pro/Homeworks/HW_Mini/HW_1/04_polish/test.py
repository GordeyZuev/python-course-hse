import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from polish import polish


def test_polish():
    assert polish(4) == "4", "число"
    assert polish(0) == "0", "ноль"
    assert polish(10) == "10", "две цифры"
    assert polish(["+", 2, 3]) == "+ 2 3"
    assert polish(["*", ["+", 2, 3], 4]) == "* + 2 3 4", "сначала левое поддерево"
    assert polish(["-", 8, ["/", 6, 2]]) == "- 8 / 6 2", "сначала правое поддерево"
    assert polish(["+", 10, 2]) == "+ 10 2"
    assert polish(["+", ["*", 2, ["-", 5, 1]], ["/", 8, 2]]) == "+ * 2 - 5 1 / 8 2"


if __name__ == "__main__":
    test_polish()
    print("тест polish прошёл")
