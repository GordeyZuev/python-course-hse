"""Открытые проверки основных требований. Полные тесты хранятся у преподавателей."""
import numpy as np
from .helpers import validate_restoration
EXAMPLE_NAMES = ('crop_image','draw_frame','calibrate','pixel_error','blue_mask',
                 'recolor_region','drop_pixels','block_preview','neighbor_stats','repair_step',
                 'restore_baseline','restore_image')


def _compare_example(actual, expected):
    if isinstance(expected, tuple):
        assert isinstance(actual, tuple) and len(actual)==len(expected), 'Верните кортеж результатов'
        for value, sample in zip(actual, expected):
            _compare_example(value, sample)
    else:
        assert isinstance(actual, np.ndarray), 'Ожидается ndarray'
        assert actual.shape == expected.shape, f'Ожидается форма {expected.shape}'
        if expected.dtype == np.dtype('int64'):
            assert np.issubdtype(actual.dtype, np.integer), 'Количество должно быть целым'
        else:
            assert actual.dtype == expected.dtype, f'Нужен dtype {expected.dtype}, получен {actual.dtype}'
        np.testing.assert_allclose(actual, expected, rtol=1e-7, atol=1e-8)


def _call_example(function, *args):
    snapshots=[(value,value.copy()) for value in args if isinstance(value,np.ndarray)]
    try:
        return function(*args)
    finally:
        for value,before in snapshots:
            np.testing.assert_array_equal(value,before,err_msg='Изменён входной массив')


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
    if name in samples:
        args,expected=samples[name]
        actual=_call_example(function,*args)
        _compare_example(actual,expected)
        if name in ('crop_image','draw_frame','calibrate','recolor_region','repair_step'):
            outputs=actual if isinstance(actual,tuple) else (actual,)
            for output in outputs:
                assert not any(np.shares_memory(output,a) for a in args if isinstance(a,np.ndarray)), 'Нужна независимая копия результата'
        if name=='repair_step':
            np.testing.assert_array_equal(actual[0][~args[1]],args[0][~args[1]],
                                          err_msg='Известные пиксели должны сохраниться точно')
        if name=='neighbor_stats':
            a=np.zeros((1,1,3),np.uint8)
            total,count=_call_example(function,a,np.ones((1,1),bool))
            _compare_example((total,count),(np.zeros((1,1,3)),np.zeros((1,1),np.int64)))
    elif name=='drop_pixels':
        original=np.full((2,3,3),100,np.uint8)
        before_rng=np.random.get_state()
        damaged,mask=_call_example(function,original,2,42)
        assert mask.shape==(2,3) and mask.dtype==bool and mask.sum()==2
        assert damaged.shape==original.shape and damaged.dtype==np.uint8
        assert not np.shares_memory(damaged,original), 'Нужна независимая копия'
        assert np.all(damaged[mask]==0)
        np.testing.assert_array_equal(damaged[~mask],original[~mask])
        again,same=_call_example(function,original,2,42)
        np.testing.assert_array_equal(damaged,again)
        np.testing.assert_array_equal(mask,same)
        after_rng=np.random.get_state()
        assert before_rng[0]==after_rng[0] and before_rng[2:]==after_rng[2:], 'Изменён глобальный RNG'
        np.testing.assert_array_equal(before_rng[1],after_rng[1],err_msg='Изменён глобальный RNG')
    else:
        damaged=np.full((3,4,3),100,np.uint8)
        mask=np.zeros((3,4),bool);mask[1,2]=True;damaged[mask]=0
        out=_call_example(function,damaged,mask)
        validate_restoration(out,damaged,mask)
        if name == 'restore_baseline':
            np.testing.assert_allclose(out, 100., err_msg='Единственный пропуск окружён цветом 100 и должен быть заполнен')


def check_task(name,function,*,verbose=True):
    try:
        if not callable(function): raise NotImplementedError
        _run_example(name,function)
    except NotImplementedError:
        result={'passed':False,'message':'Решение пока не написано'}
    except Exception as error:
        result={'passed':False,'message':f'{type(error).__name__}: {error}'}
    else:
        result={'passed':True,'message':'Примеры и основные требования пройдены'}
    if verbose: print(f"{name}: {result['message']}")
    return result


def report(namespace):
    result={name:check_task(name,namespace.get(name)) for name in EXAMPLE_NAMES}
    print(f"Примеры пройдены: {sum(v['passed'] for v in result.values())}/{len(result)}. Полная проверка выполняется отдельно.")
    return result

