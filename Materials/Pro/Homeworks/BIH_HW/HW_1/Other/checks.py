"""Те же проверки, которые выполняются при сдаче домашней работы."""

from .grading_checks import check_task, report


def check_dependencies(namespace, *names):
    """Проверить функции перед запуском опыта на фотографии."""
    ready = True
    for name in names:
        result = check_task(name, namespace.get(name), verbose=False)
        if not result['passed']:
            ready = False
            print(f'Опыт на фотографии не запущен: сначала исправьте и выполните {name}.')
            print(result['message'])
    return ready
