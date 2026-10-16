import importlib.util
from pathlib import Path

# Имя `html` уже занято стандартной библиотекой: pytest подхватывает её раньше файла задачи.
_file = Path(__file__).resolve().parent / "html.py"
_spec = importlib.util.spec_from_file_location("hw_html", _file)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
html = _module.html


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


def test_html():
    calls = []

    @html("p")
    def line():
        calls.append(1)
        return "ночь"

    assert calls == [], "украшение не вызывает функцию"
    assert line() == "<p>ночь</p>", "один тег"

    @html("div")
    @html("p")
    def paired():
        """низ"""
        return "ночь"

    assert paired() == "<div><p>ночь</p></div>", "верхняя обёртка снаружи"
    assert paired.__name__ == "paired", "имя нижней функции"
    assert paired.__doc__ == "низ", "документация нижней функции"

    @html("article")
    @html("div")
    @html("p")
    def deep():
        return "ночь"

    assert deep() == "<article><div><p>ночь</p></div></article>", "три уровня"

    @html("")
    def empty_tag():
        return "ночь"

    assert empty_tag() == "<>ночь</>", "пустой тег"

    @html("p")
    def empty_text():
        return ""

    assert empty_text() == "<p></p>", "пустой текст"

    @html("p")
    def raw():
        return "a < b > c"

    assert raw() == "<p>a < b > c</p>", "знаки в тексте не экранируются"

    @html("a b")
    def loose():
        return "ночь"

    assert loose() == "<a b>ночь</a b>", "тег подставляется как есть"

    @html("123")
    def numeric():
        return "x"

    assert numeric() == "<123>x</123>", "имя HTML не проверяется"

    @html("p")
    def with_args(text, *, extra):
        return text + extra

    assert with_args("ночь", extra="!") == "<p>ночь!</p>", "аргументы доходят до нижней функции"


if __name__ == "__main__":
    test_html()
    print("тест html прошёл")
