"""Отчёт баллов по HW 1 и HW 2.

Запуск из корня репозитория курса:

    source Materials/Pro/Homeworks/HW_Mini/.venv/bin/activate
    python Other/tools/grade.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "Materials" / "Pro" / "Homeworks" / "HW_Mini"
TEST_TIMEOUT_SECONDS = 10

HW = [
    ('HW 1', 'HW_1', [
        ('№1. line', '01_line', 0.5, False),
        ('№2. ask', '02_ask', 0.5, False),
        ('№3. palindrome', '03_palindrome', 0.5, False),
        ('№4. polish', '04_polish', 0.5, False),
        ('№5. unpack', '05_unpack', 1, False),
        ('№6. tune', '06_tune', 1, False),
        ('№7. make_fader', '07_make_fader', 1, False),
        ('№8. partial', '08_partial', 1, False),
        ('№9. vandal', '09_vandal', 0.5, False),
        ('№10. shabbat', '10_shabbat', 1, True),
        ('№11. counted', '11_counted', 0.5, False),
        ('№12. html', '12_html', 1, False),
        ('№13. fragile', '13_fragile', 1, False),
        ('№14. memoize', '14_memoize', 1, False),
        ('№15. silent', '15_silent', 1, True),
    ]),
    ('HW 2', 'HW_2', [
        ('№1. take', '01_take', 0.5, False),
        ('№2. running', '02_running', 0.6, False),
        ('№3. chain', '03_chain', 0.7, False),
        ('№4. replay', '04_replay', 0.7, False),
        ('№5. window', '05_window', 0.8, False),
        ('№6. group_runs', '06_group_runs', 0.8, False),
        ('№7. pad_zip', '07_pad_zip', 0.8, False),
        ('№8. calls', '08_calls', 0.9, False),
        ('№9. shift', '09_shift', 0.9, False),
        ('№10. read_lines', '10_read_lines', 1, False),
        ('№11. save_total', '11_save_total', 1.1, False),
        ('№12. round_robin', '12_round_robin', 1.2, False),
    ]),
]


def fmt(value):
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:g}"


def earned(folder, name):
    script = ROOT / folder / name / "test.py"
    try:
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=script.parent,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=TEST_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(f"{folder}/{name}: проверка не завершилась за {TEST_TIMEOUT_SECONDS} с", file=sys.stderr)
        return False
    return completed.returncode == 0


def report(title, folder, tasks):
    print(title)
    required = 0
    bonus = 0
    for label, name, points, is_bonus in tasks:
        got = points if earned(folder, name) else 0
        if is_bonus:
            bonus += got
        else:
            required += got
        print(f"{label}: {fmt(got)} / {fmt(points)}")
    bonus_max = sum(points for _, _, points, is_bonus in tasks if is_bonus)
    required_max = sum(points for _, _, points, is_bonus in tasks if not is_bonus)
    print()
    if bonus_max:
        total = min(10, required + bonus)
        print(f"Обязательные: {fmt(required)} / 10")
        print(f"Бонусы: {fmt(bonus)} / {fmt(bonus_max)}")
        print(f"Итог: {fmt(total)} / 10")
    else:
        print(f"Итог: {fmt(required)} / {fmt(required_max)}")
    print()


def main():
    for title, folder, tasks in HW:
        report(title, folder, tasks)


if __name__ == "__main__":
    main()
