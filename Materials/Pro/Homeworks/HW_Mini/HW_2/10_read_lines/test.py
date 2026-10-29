import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from read_lines import read_lines


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
import tempfile
from pathlib import Path


def test_read_lines():
    def lines(data):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "script.txt"
            path.write_bytes(data)
            got = read_lines(path)
            assert inspect.isgenerator(got), "read_lines возвращает генератор"
            return list(got)

    nl = bytes([10])
    cr = bytes([13])
    assert lines(b"") == [], "пустой файл"
    assert lines(b"solo") == ["solo"], "строка без перевода"
    assert lines(b"solo" + nl) == ["solo"], "одна строка с переводом"
    assert lines(b"a" + nl + b"b" + nl) == ["a", "b"], "финальный перевод не добавляет пустую строку"
    assert lines(b"a" + nl + nl) == ["a", ""], "пустая строка в конце остаётся"
    assert lines(nl) == [""], "файл из одного перевода"
    assert lines(b" a " + nl) == [" a "], "пробелы по краям остаются"
    assert lines(b"a" + cr + nl) == ["a"], "обычный текстовый режим обрабатывает Windows-окончание"
    assert lines(b"a" + cr) == ["a"], "обычный текстовый режим обрабатывает CR-окончание"
    assert lines("ночь".encode() + nl + "эфир".encode() + nl) == ["ночь", "эфир"], "кириллица"




def test_streaming_and_resource_lifetime():
    import builtins
    import read_lines as solution
    from unittest.mock import patch
    from contextlib import ExitStack
    import inspect
    from _checks import FileProbe
    syntax(read_lines, "with")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "scenario.txt"
        path.write_text("a\nb\n", encoding="utf-8")
        opened = []
        real_open = builtins.open
        def tracked_open(*args, **kwargs):
            bound = inspect.signature(real_open).bind(*args, **kwargs)
            bound.apply_defaults()
            options = bound.arguments
            assert options["encoding"] == "utf-8", "укажите UTF-8 явно"
            assert options["newline"] is None, "используйте обычный текстовый режим: newline по умолчанию"
            probe = FileProbe(real_open(*args, **kwargs), streaming=True)
            probe.allowed = 1
            opened.append(probe)
            return probe
        with ExitStack() as patches:
            for name, value in vars(solution).copy().items():
                if value is real_open and name != "open":
                    patches.enter_context(patch.object(solution, name, tracked_open))
            patches.enter_context(patch.object(solution, "open", tracked_open, create=True))
            patches.enter_context(patch.object(builtins, "open", tracked_open))
            lines = read_lines(str(path))
            assert opened == [], "файл открывается только при начале обхода"
            assert next(lines) == "a"
            assert len(opened) == 1 and opened[0].entered, "используйте open внутри with"
            probe = opened[0]
            assert probe.reads == 1 and not probe.closed
            probe.allowed = 2
            assert next(lines) == "b"
            probe.allowed = 3
            expect(lambda: next(lines), StopIteration)
            assert probe.closed, "после полного обхода файл закрыт"
            lines = read_lines(path)
            next(lines)
            lines.close()
            assert opened[-1].closed, "close генератора закрывает файл"
            lines = read_lines(path)
            next(lines)
            expect(lambda: lines.throw(ValueError("остановка")), ValueError)
            assert opened[-1].closed, "исключение тоже закрывает файл"
            lines = read_lines(path)
            lines.close()
            assert len(opened) == 3, "незапущенный генератор не открывает файл"
        path.write_bytes(b"a\rb\r\nc\n")
        assert list(read_lines(path)) == ["a", "b", "c"]



def test_example_file():
    path = Path(__file__).with_name("scenario.txt")
    lines = read_lines(path)
    assert next(lines) == "Добрый вечер!"
    assert next(lines) == ""
    assert list(lines) == ["Сейчас прозвучат заявки слушателей.", "До встречи!"]


def test_own_implementation():
    own_iteration(read_lines, forbid_zip=False)

if __name__ == "__main__":
    run_tests(globals())
