"""Открытые проверки основных требований. Полные тесты хранятся у преподавателей."""
from contextlib import contextmanager
import traceback
import numpy as np
from .helpers import validate_restoration
EXAMPLE_NAMES = ('crop_image','draw_frame','calibrate','pixel_error','mean_error','blue_mask',
                 'recolor_region','drop_pixels','block_preview','neighbor_stats','repair_step',
                 'restore_baseline','restore_image')


class _ExampleFailure(AssertionError):
    """Ошибка с названием открытого примера."""


@contextmanager
def _case(description):
    try:
        yield
    except NotImplementedError:
        raise
    except Exception as error:
        detail = str(error).strip() or 'Проверка завершилась без пояснения причины'
        if not isinstance(error, AssertionError):
            frame = traceback.extract_tb(error.__traceback__)[-1]
            detail = f'{type(error).__name__}: {detail}\nФункция {frame.name}, строка {frame.lineno}.'
            if frame.line:
                detail += '\n' + frame.line
        raise _ExampleFailure(f'Не пройдена проверка: {description}.\n{detail}') from error


def _values(actual, expected, label='Значения результата', *, exact=False):
    actual, expected = np.asarray(actual), np.asarray(expected)
    assert actual.shape == expected.shape, (
        f'{label}: ожидалась форма {expected.shape}, получена {actual.shape}')
    same = actual == expected if exact else np.isclose(actual, expected, rtol=1e-7, atol=1e-8)
    if not np.all(same):
        if expected.size <= 12:
            wanted = np.array2string(expected, precision=10)
            received = np.array2string(actual, precision=10)
            detail = f'Ожидалось: {wanted}\nПолучено: {received}'
        else:
            index = tuple(int(i) for i in np.argwhere(~same)[0])
            detail = f'Позиция {index}: ожидалось {expected[index]!r}, получено {actual[index]!r}'
        raise AssertionError(f'{label} не совпадают.\n{detail}')


def _compare_example(actual, expected, label='Результат'):
    if isinstance(expected, tuple):
        assert isinstance(actual, tuple) and len(actual)==len(expected), 'Верните кортеж результатов'
        for number, (value, sample) in enumerate(zip(actual, expected), 1):
            _compare_example(value, sample, f'Результат №{number}')
    else:
        assert isinstance(actual, np.ndarray), f'{label}: ожидается ndarray, получен {type(actual).__name__}'
        assert actual.shape == expected.shape, f'{label}: ожидалась форма {expected.shape}, получена {actual.shape}'
        if expected.dtype == np.dtype('int64'):
            assert np.issubdtype(actual.dtype, np.integer), 'Количество должно быть целым'
        else:
            assert actual.dtype == expected.dtype, f'Нужен dtype {expected.dtype}, получен {actual.dtype}'
        _values(actual, expected, label)


def _call_example(function, *args):
    snapshots=[(index,value,value.copy()) for index,value in enumerate(args,1) if isinstance(value,np.ndarray)]
    try:
        return function(*args)
    finally:
        for index,value,before in snapshots:
            assert value.dtype == before.dtype, f'Изменён тип входного массива в аргументе №{index}'
            _values(value,before,f'Входной массив в аргументе №{index} изменён',exact=True)


def _run_example(name, function):
    line=np.repeat(np.array([[10,0,0,0,50]],np.uint8)[...,None],3,axis=2)
    missing=np.array([[False,True,True,True,False]])
    border=np.full((3,3,3),[200,50,0],np.uint8);border[1,1]=0
    samples={
        'crop_image': ((np.arange(18,dtype=np.uint8).reshape(2,3,3),0,1,2,1),np.array([[[3,4,5]],[[12,13,14]]],np.uint8)),
        'draw_frame': ((np.zeros((3,3,3),np.uint8),0,0,3,3,1,np.array([200,50,0],np.uint8)),border),
        'calibrate': ((np.array([[[60,100,140]]],np.uint8),np.array([10.,20.,40.]),np.array([110.,180.,240.])),np.full((1,1,3),127.5)),
        'pixel_error': ((np.array([[[255,0,0]]],np.uint8),np.array([[[0,255,0]]],np.uint8)),np.array([[170.]])),
        'blue_mask': ((np.array([[[10,20,40],[40,20,10],[10,20,30]]],np.uint8),2.,1.,20.),np.array([[True,False,False]])),
        'recolor_region': ((np.array([[[20,60,120],[20,60,120]]],np.uint8),np.array([[True,False]]),np.array([255.,0.,0.]),1.),np.array([[[120.,0.,0.],[20.,60.,120.]]])),
        'block_preview': ((np.repeat(np.arange(16,dtype=np.uint8).reshape(4,4,1),3,axis=2),2),np.repeat(np.array([[2.5,4.5],[10.5,12.5]])[...,None],3,axis=2)),
        'neighbor_stats': ((line,missing),(np.repeat(np.array([[0.,10.,0.,50.,0.]])[...,None],3,axis=2),np.array([[0,1,0,1,0]],np.int64))),
        'repair_step': ((line,missing),(np.repeat(np.array([[10.,10.,0.,50.,50.]])[...,None],3,axis=2),np.array([[False,False,True,False,False]]))),
    }
    if name == 'mean_error':
        diff = np.array([[0., 30., 90.]])
        selected = np.array([[False, True, True]])
        for args, expected, label in [
            ((diff,),40.,'без маски, ошибки [[0, 30, 90]]'),
            ((diff,selected),60.,'с маской, выбраны ошибки [30, 90]'),
            ((np.array([[0.,90.]]),np.array([[True,False]])),0.,'выбран один пиксель с нулевой ошибкой'),
        ]:
            with _case(label):
                actual = _call_example(function, *args)
                assert isinstance(actual, (float, np.floating)), f'Верните вещественное число, получен {type(actual).__name__}'
                _values(actual, expected)
        return
    if name in samples:
        args,expected=samples[name]
        with _case('основной пример ' + name):
            actual=_call_example(function,*args)
            _compare_example(actual,expected)
            if name in ('crop_image','draw_frame','calibrate','recolor_region','repair_step'):
                outputs=actual if isinstance(actual,tuple) else (actual,)
                for output in outputs:
                    assert not any(np.shares_memory(output,a) for a in args if isinstance(a,np.ndarray)), 'Нужна независимая копия результата'
            if name=='repair_step':
                _values(actual[0][~args[1]],args[0][~args[1]],'Известные пиксели',exact=True)
        if name=='pixel_error':
            for dtype in (np.float16,np.float32,np.float64):
                with _case(f'дробные цвета {np.dtype(dtype)}, ошибки в двух пикселях'):
                    source=np.array([[[0.25,100.5,254.75],[1.5,2.5,3.5]]],dtype=dtype)
                    candidate=np.array([[[1.75,99.,253.25],[1.5,2.5,3.5]]],dtype=dtype)
                    _compare_example(_call_example(function,source,candidate),np.array([[1.5,0.]]))
                with _case(f'сравнение uint8 и {np.dtype(dtype)}'):
                    source=np.array([[[0,100,255]]],dtype=np.uint8)
                    candidate=np.array([[[1.5,98.5,253.5]]],dtype=dtype)
                    _compare_example(_call_example(function,source,candidate),np.array([[1.5]]))
        if name=='neighbor_stats':
            with _case('изображение 1 × 1 без известных соседей'):
                a=np.zeros((1,1,3),np.uint8)
                result=_call_example(function,a,np.ones((1,1),bool))
                _compare_example(result,(np.zeros((1,1,3)),np.zeros((1,1),np.int64)))
    elif name=='drop_pixels':
        with _case('два пропуска на изображении 2 × 3, seed=42'):
            original=np.full((2,3,3),100,np.uint8)
            before_rng=np.random.get_state()
            result=_call_example(function,original,2,42)
            assert isinstance(result,tuple) and len(result)==2, 'Верните кортеж (damaged, missing)'
            damaged,mask=result
            assert isinstance(mask,np.ndarray), 'Маска missing должна быть ndarray'
            assert mask.shape==(2,3), f'Форма маски: ожидалась (2, 3), получена {mask.shape}'
            assert mask.dtype==bool, f'Тип маски: нужен bool, получен {mask.dtype}'
            assert mask.sum()==2, f'Число пропусков: ожидалось 2, получено {int(mask.sum())}'
            assert isinstance(damaged,np.ndarray), 'Повреждённое изображение должно быть ndarray'
            assert damaged.shape==original.shape, f'Форма изображения: ожидалась {original.shape}, получена {damaged.shape}'
            assert damaged.dtype==np.uint8, f'Тип изображения: нужен uint8, получен {damaged.dtype}'
            assert not np.shares_memory(damaged,original), 'Нужна независимая копия изображения'
            _values(damaged[mask],np.zeros_like(damaged[mask]),'Каналы потерянных пикселей',exact=True)
            _values(damaged[~mask],original[~mask],'Пиксели вне маски',exact=True)
            repeated=_call_example(function,original,2,42)
            assert isinstance(repeated,tuple) and len(repeated)==2, 'Повторный вызов должен вернуть кортеж (damaged, missing)'
            again,same=repeated
            _values(again,damaged,'Изображения при одинаковом seed',exact=True)
            _values(same,mask,'Маски при одинаковом seed',exact=True)
            after_rng=np.random.get_state()
            assert before_rng[0]==after_rng[0] and before_rng[2:]==after_rng[2:], 'Изменено глобальное состояние генератора случайных чисел'
            _values(after_rng[1],before_rng[1],'Глобальное состояние генератора случайных чисел',exact=True)
    else:
        with _case('один пропуск на изображении 3 × 4, известные цвета равны 100'):
            damaged=np.full((3,4,3),100,np.uint8)
            mask=np.zeros((3,4),bool);mask[1,2]=True;damaged[mask]=0
            out=_call_example(function,damaged,mask)
            validate_restoration(out,damaged,mask)
            if name == 'restore_baseline':
                _values(out,np.full(out.shape,100.),'Восстановление единственного пропуска')


def check_task(name,function,*,verbose=True):
    try:
        if name not in EXAMPLE_NAMES:
            raise ValueError(f'Неизвестная проверка: {name}')
        if not callable(function): raise NotImplementedError
        _run_example(name,function)
    except NotImplementedError:
        result={'passed':False,'message':'Решение пока не написано'}
    except _ExampleFailure as error:
        result={'passed':False,'message':str(error)}
    except Exception as error:
        result={'passed':False,'message':f'{type(error).__name__}: {error}'}
    else:
        result={'passed':True,'message':'Примеры и основные требования пройдены'}
    if verbose: print(f"{name}: {result['message']}")
    return result


def check_dependencies(namespace, *names):
    """Проверяем текущие функции, чтобы опыт не использовал старый результат проверки."""
    ready=True
    for name in names:
        result=check_task(name,namespace.get(name),verbose=False)
        if not result['passed']:
            ready=False
            print(f'Опыт на фотографии не запущен: сначала исправьте и выполните {name}.')
            print(result['message'])
    return ready


def report(namespace):
    result={name:check_task(name,namespace.get(name)) for name in EXAMPLE_NAMES}
    print(f"Примеры пройдены: {sum(v['passed'] for v in result.values())}/{len(result)}. Полная проверка выполняется отдельно.")
    return result

