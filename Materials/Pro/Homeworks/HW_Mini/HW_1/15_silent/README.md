#### **№15. Тишина в эфире. · Бонус · 1 балл**

**Бонус. 1 балл.**

Представим, что идет эфир! Любая ошибка – не должна нарушать его! Мы должны написать декоретор `silent(default)` так, что любой `Exception` внутри тела превращается в `default`. Функция после этого не ломается: следующий вызов снова входит в тело.

Успешный результат не подменяется. Если тело вернуло `None`, `0` или `False`, наружу идёт именно это, даже когда `default` другое.

- Ловится любой `Exception`, в том числе `KeyError`, не только два-три типа.
- `SystemExit` и `KeyboardInterrupt` не ловятся: это не `Exception`. Они выходят как есть.
- Наружу при ошибке возвращается сам объект `default`, не копия.
- `default` может быть `0`, `None`, `False` или строка. Ноль здесь не значит «значения не было».
- Украшение само функцию не вызывает.
- У двух функций две обёртки. Аргументы доходят до тела.
- Снаружи видны `__name__` и `__doc__` исходной функции. Для этого подходит `functools.wraps`.

Что такое исключение: [Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html).

```python
@silent(0)
def level():
    raise ValueError("тишина")

level()  # -> 0
```

```python
@silent("тихо")
def missing():
    raise KeyError("нет ключа")

missing()  # -> тихо
```

```python
@silent(0)
def give():
    return None

give()  # -> None
```

```python
@silent(None)
def give_zero():
    return 0

give_zero()  # -> 0
```

```python
marker = ["тихо"]

@silent(marker)
def fail():
    raise RuntimeError("нет")

fail()  # тот же список marker
```

## **Как это сделать.**

В обёртке поймайте вызов через `try`. Любой `Exception` отдаёт тот же объект `default`. Успех возвращайте как есть.

## **Как запустить эти тесты.**

Из папки этой задачи:

```bash
python test.py
```

Из корня `HW_Mini`:

```bash
pytest HW_1/15_silent/test.py
```

Как собрать среду с нуля: [общая инструкция](../../README.md).
