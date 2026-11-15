"""Локальный отчёт баллов по опубликованным ДЗ.

Запуск из корня репозитория курса:

    source Materials/Pro/Homeworks/HW_Mini/.venv/bin/activate
    python Other/tools/grade.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "Materials" / "Pro" / "Homeworks" / "HW_Mini"
TEST_TIMEOUT_SECONDS = 10

import json
import argparse
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "grading"))
from manifest import load_assignments
MANIFEST = load_assignments(Path(__file__).resolve().parents[2])
def fmt(value):
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:g}"


def earned(folder, name):
    script = ROOT / folder / name / "test.py"
    try:
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[1] / "grading" / "container_check.py"), "--local", str(script)],
            cwd=script.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=TEST_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(f"{folder}/{name}: проверка не завершилась за {TEST_TIMEOUT_SECONDS} с", file=sys.stderr)
        return False
    return completed.returncode == 0 and completed.stdout == b"course-tests-completed\n"


def report(hw):
    print(hw['title'])
    if hw.get('submission'):
        notebook=Path(__file__).resolve().parents[2] / hw['path'] / hw['submission']
        earned_auto=0
        for task in hw['tasks']:
            if task['mode']=='manual':
                print(f'{task["label"]}: проверит ассистент')
                continue
            try:
                completed=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'grading/notebook_check.py'),
                                          str(notebook),task['function']],cwd=notebook.parent,
                                         stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,timeout=TEST_TIMEOUT_SECONDS)
                passed=completed.returncode==0
                if not passed and completed.stderr:
                    print('  '+completed.stderr.strip().splitlines()[-1])
            except subprocess.TimeoutExpired:passed=False
            got=task['points'] if passed else 0
            earned_auto+=got
            print(f'{task["label"]}: {fmt(got)} / {fmt(task["points"])}')
        print(f'Автоматический результат: {fmt(earned_auto)} / 5\n')
        return
    folder=os.path.relpath(Path(__file__).resolve().parents[2] / hw['path'],ROOT)
    tasks=[(t['label'],t['id'],t['points'],t['bonus']) for t in hw['tasks']]
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--hw", choices=MANIFEST)
    args = parser.parse_args()
    for key,hw in MANIFEST.items():
        if args.hw is None or key == args.hw:
            report(hw)


if __name__ == "__main__":
    main()
