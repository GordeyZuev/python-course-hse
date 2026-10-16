# 14. Memoize

def memoize(func):
    ...

# Оставляйте только декоратор memoize.
# Для запуска тестов: python -m pytest test.py.
#
# Сравните Фибоначчи с декоратором и без него.
# На 40-м числе разница во времени уже заметна.
# Рекурсия должна звать ту же функцию, которую вы украсили:
# иначе кэш на внутренних вызовах не работает.
#
# def fib(n):
#     if n < 2:
#         return n
#     return fib(n - 1) + fib(n - 2)
#
# @memoize
# def fib_fast(n):
#     if n < 2:
#         return n
#     return fib_fast(n - 1) + fib_fast(n - 2)
#
# fib(40)       # долго
# fib_fast(40)  # сразу
