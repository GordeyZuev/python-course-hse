"""Общие проверки учебных конструкций и наблюдения за чтением источника."""
import ast
import inspect
import textwrap


def syntax(function, kind):
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    nodes = list(ast.walk(tree))
    if kind == "yield_from":
        ok = any(isinstance(node, ast.YieldFrom) for node in nodes)
        message = "используйте yield from для передачи обхода"
    elif kind == "value_error":
        ok = any(isinstance(node, ast.Try)
                 and any(isinstance(part, ast.Yield) for statement in node.body for part in ast.walk(statement))
                 and any(handler.type is not None for handler in node.handlers)
                 for node in nodes)
        message = "yield заказа должен быть внутри try / except с указанным типом исключения"
    elif kind == "finally":
        ok = any(isinstance(node, ast.Try) and node.finalbody for node in nodes)
        message = "для завершения смены нужен try / finally"
    elif kind == "with":
        ok = any(isinstance(node, ast.With) for node in nodes)
        message = "работайте с файлом через with"
    else:
        raise ValueError(kind)
    assert ok, message


class Source:
    """Источник с лимитом запросов: раннее чтение сразу даёт понятную ошибку."""
    def __init__(self, values, allowed=0):
        self.values = iter(values)
        self.allowed = allowed
        self.pulls = 0
        self.starts = 0

    def __iter__(self):
        self.starts += 1
        return self

    def __next__(self):
        self.pulls += 1
        assert self.pulls <= self.allowed, "источник прочитан раньше, чем нужен следующий результат"
        return next(self.values)


class Untouched:
    def __iter__(self):
        raise AssertionError("при этом параметре не нужно даже вызывать iter у источника")


def run_tests(namespace):
    for name, function in sorted(namespace.copy().items()):
        if name.startswith("test_") and callable(function):
            function()
    print("Все проверки задачи прошли")


class FileProbe:
    """Обёртка настоящего файла для проверки чтения и освобождения ресурса."""
    def __init__(self, handle, *, read_text=None, streaming=False):
        import io
        self.handle = handle
        self.reader = io.StringIO(read_text) if read_text is not None else handle
        self.streaming = streaming
        self.reads = 0
        self.allowed = 1000
        self.entered = False

    def __enter__(self):
        self.handle.__enter__()
        self.entered = True
        return self

    def __exit__(self, *args):
        return self.handle.__exit__(*args)

    def __iter__(self):
        return self

    def __next__(self):
        if self.handle.closed:
            raise ValueError("I/O operation on closed file")
        self.reads += 1
        assert self.reads <= self.allowed, "генератор читает следующую строку заранее"
        return next(self.reader)

    def read(self, *args):
        if self.handle.closed:
            raise ValueError("I/O operation on closed file")
        assert not self.streaming, "сценарий нужно обходить по строкам, без read()"
        self.reads += 1
        return self.reader.read(*args)

    def readlines(self, *args):
        if self.handle.closed:
            raise ValueError("I/O operation on closed file")
        assert not self.streaming, "сценарий нужно обходить по строкам, без readlines()"
        self.reads += 1
        return self.reader.readlines(*args)

    def readline(self, *args):
        if self.handle.closed:
            raise ValueError("I/O operation on closed file")
        self.reads += 1
        assert self.reads <= self.allowed, "следующая строка прочитана заранее"
        return self.reader.readline(*args)

    def seek(self, *args):
        self.handle.seek(*args)
        if self.reader is not self.handle:
            self.reader.seek(*args)

    def __getattr__(self, name):
        return getattr(self.handle, name)


def own_iteration(function, *, forbid_zip=False):
    """Не подменять учебный обход готовым аналогом из itertools."""
    module = inspect.getmodule(function)
    tree = ast.parse(inspect.getsource(module))
    forbidden = {"accumulate", "chain", "cycle", "islice", "zip_longest", "groupby", "pairwise"}
    modules = set()
    aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.asname or alias.name for alias in node.names if alias.name == "itertools")
        if isinstance(node, ast.ImportFrom) and node.module == "itertools":
            aliases.update(alias.asname or alias.name for alias in node.names if alias.name in forbidden)
            assert all(alias.name != "*" for alias in node.names), "напишите обход самостоятельно, без импорта itertools.*"
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        attributes = []
        while isinstance(func, ast.Attribute):
            attributes.append(func.attr)
            func = func.value
        ready = isinstance(func, ast.Name) and func.id in aliases
        ready |= (isinstance(func, ast.Name) and func.id in modules
                  and bool(attributes) and attributes[-1] in forbidden)
        if forbid_zip:
            ready |= isinstance(node.func, ast.Name) and node.func.id == "zip"
        assert not ready, "напишите собственный обход: готовый аналог не тренирует этот приём"
