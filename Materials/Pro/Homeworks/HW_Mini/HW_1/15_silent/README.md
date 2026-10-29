#### **№15. Тишина в эфире. · Бонус · 1 балл**

**Бонус. 1 балл.**

Представим, что идёт эфир. Любая ошибка не должна привести к его обрыву. Напишите декоратор `silent(default)`: любой `Exception` внутри тела превращается в `default`. Следующий вызов снова входит в тело.

Успешный результат не подменяется. Если тело вернуло `None`, `0` или `False`, наружу идёт именно это, даже когда `default` другое.

**Уточнения.**

- Ловится любой `Exception`, в том числе `KeyError`, `TypeError` и `RuntimeError`, не только два-три типа.
- `SystemExit` и `KeyboardInterrupt` не ловятся: это не `Exception`. Они выходят как есть.
- Наружу при ошибке возвращается сам объект `default`, не копия.
- `default` может быть любым объектом, в том числе `0`, `None`, строкой или списком. Ноль здесь не значит «значения не было».
- В момент декорирования функция не вызывается.
- Аргументы доходят до тела, в том числе по имени.

`__name__` и `__doc__` остаются от исходной функции. Возьмите `functools.wraps`. Две обёрнутые функции не делят `default`.

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

В обёртке вызовите функцию через `try`. Успех верните как есть, включая `None`, `0` и `False`. Любой `Exception` отдаёт тот же объект `default`, не копию. `SystemExit` и `KeyboardInterrupt` не ловите.

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
