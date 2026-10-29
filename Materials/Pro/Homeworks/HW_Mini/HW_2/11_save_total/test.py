import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from save_total import save_total


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

import tempfile
from pathlib import Path


def test_save_total():
    def check(numbers, preseed=None):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "log.txt"
            if preseed is not None:
                path.write_bytes(preseed)
            got = save_total(path, numbers)
            assert type(got) is int, "save_total возвращает целое число"
            return got, path.read_bytes()

    nl = bytes([10])
    assert check([], preseed=b"999" + nl) == (0, b""), "пустой список обнуляет файл и даёт 0"
    assert check([4]) == (4, b"4" + nl), "одно число"
    assert check([1, 2, 3]) == (6, b"1" + nl + b"2" + nl + b"3" + nl), "несколько чисел"
    assert check([0]) == (0, b"0" + nl), "ноль записывается как 0"
    got, text = check([10, -3, 200])
    assert got == 207, "отрицательные и многозначные входят в сумму"
    assert text == b"10" + nl + b"-3" + nl + b"200" + nl, "в файле ровно эти строки"
    got, text = check([1, 2], preseed=b"999" + nl)
    assert got == 3, "старое 999 не входит в сумму"
    assert text == b"1" + nl + b"2" + nl, "файл перезаписан, а не дополнен"




def test_sum_uses_saved_file_and_closes_handles():
    import builtins
    import save_total as solution
    from unittest.mock import patch
    from contextlib import ExitStack
    import inspect
    from _checks import FileProbe
    syntax(save_total, "with")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "journal.txt"
        opened = []
        real_open = builtins.open
        def tracked_open(*args, **kwargs):
            bound = inspect.signature(real_open).bind(*args, **kwargs)
            bound.apply_defaults()
            options = bound.arguments
            assert options["encoding"] == "utf-8", "укажите UTF-8 явно"
            mode = options["mode"]
            if "w" in mode:
                assert options["newline"] == "\n", "при записи нужен newline=\\n"
            handle = real_open(*args, **kwargs)
            # Меняем только данные чтения: так видно, откуда взят итог.
            probe = FileProbe(handle, read_text="7\n-2\n")
            opened.append(probe)
            return probe
        with ExitStack() as patches:
            for name, value in vars(solution).copy().items():
                if value is real_open and name != "open":
                    patches.enter_context(patch.object(solution, name, tracked_open))
            patches.enter_context(patch.object(solution, "open", tracked_open, create=True))
            patches.enter_context(patch.object(builtins, "open", tracked_open))
            got = save_total(str(path), [10, 20])
        assert got == 5, "итог должен зависеть от прочитанных строк, а не от numbers"
        assert path.read_bytes() == b"10\n20\n", "записываются исходные числа"
        assert opened and sum(p.reads for p in opened) > 0, "нужно прочитать записанный файл"
        assert all(p.entered and p.closed for p in opened), "каждый файл открывается через with и закрывается"



def test_own_implementation():
    own_iteration(save_total, forbid_zip=False)

if __name__ == "__main__":
    run_tests(globals())
