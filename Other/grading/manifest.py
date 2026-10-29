"""The sole homework configuration reader, shared by local grading and releases."""
import datetime as dt
import json
import math
from pathlib import Path
import re


def component(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', value) and value not in ('.', '..')


def load_assignments(root):
    root = Path(root).resolve()
    assignments = {}
    for config in sorted((root / 'Materials').rglob('homework.json')):
        # Ignore local virtual environments and symlinked directories.
        if any(part.startswith('.') for part in config.relative_to(root).parts):
            continue
        if config.is_symlink() or not config.resolve().is_relative_to(root):
            raise ValueError(f'Configuration outside course: {config}')
        value = json.loads(config.read_text(encoding='utf-8'))
        if not isinstance(value, dict) or type(value.get('enabled')) is not bool:
            raise ValueError(f'{config}: enabled must be true or false')
        if not value['enabled']:
            continue
        unknown = value.keys() - {'id', 'enabled', 'title', 'deadline', 'attempts', 'tasks', 'dependencies'}
        if unknown:
            raise ValueError(f'{config}: unknown settings: {sorted(unknown)}')
        key = value.get('id')
        if not isinstance(key, str) or not re.fullmatch(r'[a-z][a-z0-9]*(-[a-z0-9]+)*', key) or key in assignments:
            raise ValueError(f'{config}: invalid or duplicate homework id')
        if not isinstance(value.get('title'), str) or not value['title'].strip():
            raise ValueError(f'{key}: title is required')
        try:
            deadline = dt.datetime.fromisoformat(value['deadline'].replace('Z', '+00:00'))
        except (KeyError, TypeError, AttributeError, ValueError) as error:
            raise ValueError(f'{key}: deadline must be an ISO date and time with a timezone') from error
        if deadline.tzinfo is None:
            raise ValueError(f'{key}: deadline needs a timezone')
        if type(value.get('attempts')) is not int or value['attempts'] < 1:
            raise ValueError(f'{key}: attempts must be a positive integer')
        tasks = value.get('tasks')
        if not isinstance(tasks, list) or not tasks:
            raise ValueError(f'{key}: at least one task is required')
        seen = set()
        for task in tasks:
            if not isinstance(task, dict) or task.keys() != {'id', 'label', 'points', 'bonus', 'solution'}:
                raise ValueError(f'{key}: task needs id, label, points, bonus, solution')
            if not component(task['id']) or task['id'] in seen:
                raise ValueError(f'{key}: invalid or duplicate task id')
            seen.add(task['id'])
            if not component(task['solution']) or not task['solution'].endswith('.py') or task['solution'] == 'test.py':
                raise ValueError(f'{key}: solution must be a Python filename other than test.py')
            if type(task['points']) not in (int, float) or not math.isfinite(task['points']) or not 0 < task['points'] <= 10:
                raise ValueError(f'{key}: invalid task points')
            if type(task['bonus']) is not bool or not isinstance(task['label'], str) or not task['label'].strip():
                raise ValueError(f'{key}: invalid task label or bonus')
            for name in (task['solution'], 'test.py'):
                path = config.parent / task['id'] / name
                if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(config.parent.resolve()):
                    raise ValueError(f'{key}: missing or unsafe file: {path}')
        dependencies = value.get('dependencies', [])
        if not isinstance(dependencies, list) or any(not isinstance(item, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*==[A-Za-z0-9][A-Za-z0-9_.+!-]*', item) for item in dependencies):
            raise ValueError(f'{key}: dependencies must be pinned package==version strings')
        assignments[key] = {k: v for k, v in value.items() if k not in ('id', 'enabled')}
        assignments[key].update(path=config.parent.relative_to(root).as_posix(), dependencies=dependencies)
        if any(char in assignments[key]['path'] for char in '*?[]\n\r'):
            raise ValueError(f'{key}: homework path must not contain GitHub glob characters or newlines')
    if not assignments:
        raise ValueError('No enabled homework.json found under Materials')
    folders = [hw['path'] for hw in assignments.values()]
    if any(a != b and a.startswith(b + '/') for a in folders for b in folders):
        raise ValueError('Homework folders must not be nested inside each other')
    return assignments


if __name__ == '__main__':
    result = load_assignments(Path(__file__).resolve().parents[2])
    print(json.dumps(result, ensure_ascii=False, indent=2))
