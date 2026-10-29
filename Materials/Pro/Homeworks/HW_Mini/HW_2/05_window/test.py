import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _checks import Source, Untouched, syntax, run_tests, own_iteration

sys.path.insert(0, str(Path(__file__).resolve().parent))

from window import window


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


class _Explode:
    def __iter__(self):
        return self

    def __next__(self):
        raise AssertionError("источник читали")


def test_window():
    expect(lambda: list(window(_Explode(), 0)), ValueError)
    expect(lambda: list(window(_Explode(), -1)), ValueError)
    assert list(window([], 2)) == [], "пустой источник"
    assert list(window([1, 2], 3)) == [], "источник короче окна"
    got = list(window([1, 2], 1))
    assert got == [(1,), (2,)], "окно длины 1"
    assert all(isinstance(item, tuple) for item in got), "кортежи, не списки"
    assert list(window([1, 2, 3, 4], 2)) == [(1, 2), (2, 3), (3, 4)], "шаг 1"
    assert list(window([1, 2, 3], 3)) == [(1, 2, 3)], "окно на всю длину"

    def source():
        yield from [1, 2, 3, 4]

    assert list(window(source(), 2)) == list(window([1, 2, 3, 4], 2)), "генератор даёт те же окна"
    assert inspect.isgenerator(window([1], 1)), "window возвращает генератор"

    def lazy():
        yield 1
        yield 2
        raise AssertionError("третье число раньше второго окна")

    step = window(lazy(), 2)
    assert next(step) == (1, 2), "первое окно не тянет лишний элемент"


def test_all_window_steps():
    invalid = window(Untouched(), 0)
    assert inspect.isgenerator(invalid), "ошибка возникает при обходе, а не при создании генератора"
    expect(lambda: next(invalid), ValueError)
    markers = [[], [], [], []]
    source = Source(markers)
    result = window(source, 2)
    assert source.pulls == 0
    windows = []
    for i in range(3):
        source.allowed = i + 2
        item = next(result)
        assert type(item) is tuple and len(item) == 2
        assert item[0] is markers[i] and item[1] is markers[i + 1]
        windows.append(item)
    assert windows[0][0] is markers[0], "старое окно не меняется при сдвиге"



def test_own_implementation():
    own_iteration(window, forbid_zip=False)


def test_old_elements_are_released():
    import gc
    import weakref
    class Item:
        pass
    live = weakref.WeakSet()
    def source():
        for _ in range(80):
            item = Item()
            live.add(item)
            yield item
    windows = window(source(), 3)
    try:
        for _ in range(50):
            frame = next(windows)
            assert len(frame) == 3
        gc.collect()
        # Запас допускает временные переменные и несколько копий буфера.
        assert len(live) <= 16, "храните текущее окно, а не всю историю источника"
    finally:
        windows.close()


if __name__ == "__main__":
    run_tests(globals())
