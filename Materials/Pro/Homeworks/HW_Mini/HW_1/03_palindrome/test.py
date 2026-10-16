import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from palindrome import is_palindrome


def test_palindrome():
    assert is_palindrome("") is True, "пустая строка"
    assert is_palindrome("а") is True, "один символ"
    assert is_palindrome(" ") is True, "один пробел"
    assert is_palindrome("аа") is True
    assert is_palindrome("аб") is False
    assert is_palindrome("абба") is True
    assert is_palindrome("аббаа") is False
    assert is_palindrome("казак") is True
    assert is_palindrome("Казак") is False, "регистр различается"
    assert is_palindrome("а а") is True, "пробел – обычный символ"
    assert is_palindrome("аб а") is False
    assert is_palindrome("abcba") is True
    assert is_palindrome("abca") is False


if __name__ == "__main__":
    test_palindrome()
    print("тест palindrome прошёл")
