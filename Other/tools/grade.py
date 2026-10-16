"""Отчёт баллов по HW 1 и HW 2.

Запуск из корня репозитория курса:

    source Materials/Pro/Homeworks/HW_Mini/.venv/bin/activate
    python Other/tools/grade.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "Materials" / "Pro" / "Homeworks" / "HW_Mini"

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
        ('№1. take', '01_take', 1, False),
        ('№2. running', '02_running', 1, False),
        ('№3. window', '03_window', 1, False),
        ('№4. chain', '04_chain', 1, False),
        ('№5. group_runs', '05_group_runs', 1, False),
        ('№6. pad_zip', '06_pad_zip', 1, False),
        ('№7. replay', '07_replay', 1.5, False),
        ('№8. read_lines', '08_read_lines', 1, False),
        ('№9. save_total', '09_save_total', 1.5, False),
        ('№10. totaler', '10_totaler', 1, True),
        ('№11. read_chunks', '11_read_chunks', 1, True),
    ]),
]


def fmt(value):
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:g}"


def earned(folder, name):
    script = ROOT / folder / name / "test.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=script.parent,
        capture_output=True,
        text=True,
    )
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
    total = min(10, required + bonus)
    bonus_max = sum(points for _, _, points, is_bonus in tasks if is_bonus)
    print()
    print(f"Обязательные: {fmt(required)} / 10")
    print(f"Бонусы: {fmt(bonus)} / {fmt(bonus_max)}")
    print(f"Итог: {fmt(total)} / 10")
    print()


def main():
    for title, folder, tasks in HW:
        report(title, folder, tasks)


if __name__ == "__main__":
    main()
