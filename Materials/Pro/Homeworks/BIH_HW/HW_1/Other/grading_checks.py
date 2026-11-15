"""Полные проверки BIH HW 1 для преподавателя; исследование оценивает ассистент."""
import numpy as np
from Other.helpers import validate_restoration

TASKS = {
    'crop_image': .3, 'draw_frame': .3, 'calibrate': .3, 'pixel_error': .4, 'mean_error': .4,
    'blue_mask': .4, 'recolor_region': .5, 'drop_pixels': .5,
    'block_preview': .6, 'neighbor_stats': .6, 'repair_step': .7,
}


def call(function, *args):
    snapshots = [(value, value.copy()) for value in args if isinstance(value, np.ndarray)]
    try:
        return function(*args)
    finally:
        for value, before in snapshots:
            assert value.dtype == before.dtype, 'Изменён тип входного массива'
            np.testing.assert_array_equal(value, before, err_msg='Изменён входной массив')


def array(actual, expected, dtype=None, *, atol=1e-8):
    assert isinstance(actual, np.ndarray), 'Ожидается ndarray'
    expected = np.asarray(expected)
    assert actual.shape == expected.shape, f'Форма {actual.shape}, ожидается {expected.shape}'
    if dtype is not None:
        assert actual.dtype == np.dtype(dtype), f'dtype: нужен {np.dtype(dtype)}, получен {actual.dtype}'
    np.testing.assert_allclose(actual, expected, rtol=1e-7, atol=atol, equal_nan=True)


def input_precision_tolerance(dtype):
    return max(1e-8, float(np.finfo(dtype).eps) * 255)


def floating_array(actual, expected, *input_dtypes):
    assert isinstance(actual, np.ndarray), 'Ожидается ndarray'
    assert np.issubdtype(actual.dtype, np.floating), (
        f'dtype: нужен вещественный массив, получен {actual.dtype}')
    atol = max(input_precision_tolerance(dtype) for dtype in (*input_dtypes, actual.dtype))
    array(actual, expected, atol=atol)


def raises_value_error(function, *args):
    try:
        call(function, *args)
    except ValueError:
        return
    raise AssertionError('Ожидается ValueError')


def images():
    rng = np.random.default_rng(182)
    return [np.array([[[0, 128, 255]]], np.uint8),
            rng.integers(0, 256, (1, 5, 3), dtype=np.uint8),
            rng.integers(0, 256, (5, 1, 3), dtype=np.uint8),
            rng.integers(0, 256, (5, 7, 3), dtype=np.uint8),
            rng.integers(0, 256, (10, 12, 3), dtype=np.uint8)[::2, ::2],
            rng.integers(0, 256, (7, 9, 3), dtype=np.uint8)[::-1, ::-1]]


def test_crop_image(f):
    for a in images():
        h, w = a.shape[:2]
        rectangles=[(0,0,h,w),(h-1,w-1,1,1),(0,0,1,w)]
        if h>=5 and w>=5: rectangles.append((1,2,h-2,w-3))
        for top, left, height, width in rectangles:
            expected = np.array([[a[y,x].tolist() for x in range(left,left+width)]
                                 for y in range(top,top+height)],np.uint8)
            out = call(f,a,top,left,height,width)
            array(out,expected,np.uint8)
            assert not np.shares_memory(out,a), 'Нужен независимый фрагмент'


def test_draw_frame(f):
    for a in images():
        h,w=a.shape[:2]
        rectangles=[(0,0,h,w),(h-1,w-1,1,1),(0,0,max(1,h-1),max(1,w-1))]
        if h>=5 and w>=5: rectangles.append((1,1,h-2,w-2))
        for top,left,height,width in rectangles:
            for thickness in range(1,min(height,width)+1):
                for color in [np.array([255,0,73],np.uint8), np.zeros(3,np.uint8),
                              np.array([2,254,17],np.uint8)[::-1]]:
                    expected=a.copy()
                    for y in range(top,top+height):
                        for x in range(left,left+width):
                            if min(y-top,top+height-1-y,x-left,left+width-1-x)<thickness:
                                expected[y,x]=color
                    out=call(f,a,top,left,height,width,thickness,color)
                    array(out,expected,np.uint8)
                    assert not np.shares_memory(out,a)


def test_calibrate(f):
    for a in images():
        for black,white in [(np.zeros(3),np.full(3,255.)),(np.array([20.,40.,60.]),np.array([180.,200.,220.])),(np.array([0.,100.,200.]),np.array([1.,101.,201.]))]:
            expected=np.empty(a.shape,float)
            for y,x,c in np.ndindex(a.shape):
                expected[y,x,c]=min(255,max(0,(float(a[y,x,c])-black[c])*255/(white[c]-black[c])))
            out=call(f,a,black,white)
            floating_array(out,expected,black.dtype,white.dtype)
            assert not np.shares_memory(out,a)


    # Real-valued parameter vectors are not restricted to float64 in the task.
    for dtype in [np.float16,np.float32,np.float64]:
        a=np.array([[[80,125,200],[200,100,20]]],np.uint8)
        black=np.array([11.3,37.7,85.1],dtype=dtype)
        white=np.array([180.8,220.2,250.7],dtype=dtype)
        expected=np.clip((a.astype(float)-black.astype(float))*255/
                         (white.astype(float)-black.astype(float)),0,255)
        # Учитываем точность входных параметров и результата.
        floating_array(call(f,a,black,white),expected,dtype)


def test_pixel_error(f):
    for a in images():
        for b in [255-a,np.zeros(a.shape,np.uint8),a.copy(),a.astype(float)/2+.25]:
            for source in [a,a.astype(float),a.astype(float)/2+.125]:
                expected=np.empty(a.shape[:2],float)
                for y,x in np.ndindex(expected.shape):
                    expected[y,x]=sum(abs(float(source[y,x,c])-float(b[y,x,c])) for c in range(3))/3
                array(call(f,source,b),expected,np.float64)
    # Восстановления проекта могут возвращать любой вещественный тип.
    for dtype_a in (np.uint8,np.float16,np.float32,np.float64,np.longdouble):
        for dtype_b in (np.uint8,np.float16,np.float32,np.float64,np.longdouble):
            source=np.array([[[0.125,100.3,254.75],[255.,0.,64.1]]],dtype=dtype_a)
            candidate=np.array([[[1.75,99.2,253.25],[0.,255.,64.3]]],dtype=dtype_b)
            for a,b in [(source,candidate),(candidate[...,::-1],source[...,::-1])]:
                expected=np.empty(a.shape[:2],np.float64)
                for y,x in np.ndindex(expected.shape):
                    expected[y,x]=sum(abs(float(a[y,x,c])-float(b[y,x,c])) for c in range(3))/3
                array(call(f,a,b),expected,np.float64)


def test_blue_mask(f):
    examples=images()+[np.array([[[10,20,30],[30,20,10],[0,0,0],[10,20,40],[0,0,255],[20,1,40],[1,20,40],[10,5,30],[1,1,2]]],np.uint8)]
    for a in examples:
        for rr,gr,gap in [(1.15,1.05,12),(2.,1.,20),(0.,0.,0),(1.,1.,255),(2.,1.,0),(1.,2.,0),(1.,1.,20)]:
            expected=np.empty(a.shape[:2],bool)
            for y,x in np.ndindex(expected.shape):
                r,g,b=map(float,a[y,x]);expected[y,x]=b>rr*r and b>gr*g and b-r>gap
            array(call(f,a,rr,gr,gap),expected,bool)


def test_recolor_region(f):
    rng=np.random.default_rng(198)
    for a in images():
        for mask in [np.zeros(a.shape[:2],bool),np.ones(a.shape[:2],bool),rng.random(a.shape[:2])<.5]:
            for color in [np.array([230.,65.,95.]),np.array([0.,255.,0.]),np.ones(3)]:
                for strength in [0.,.35,1.]:
                    expected=a.astype(float)
                    for y,x in np.ndindex(mask.shape):
                        if mask[y,x]:
                            value=max(map(float,a[y,x]))
                            for c in range(3):
                                expected[y,x,c]=(1-strength)*float(a[y,x,c])+strength*value*float(color[c])/max(color)
                    out=call(f,a,mask,color,strength)
                    floating_array(out,expected,color.dtype)
                    np.testing.assert_array_equal(out[~mask],a[~mask])
                    assert not np.shares_memory(out,a)


    for dtype in [np.float16,np.float32,np.float64]:
        a=np.array([[[20,60,120],[240,10,80]]],np.uint8)
        mask=np.array([[True,False]])
        color=np.array([230.3,65.2,95.7],dtype=dtype)
        strength=dtype(.35)
        c=color.astype(float);alpha=float(strength)
        expected=a.astype(float)
        expected[mask]=(1-alpha)*expected[mask]+alpha*a.max(axis=2)[mask,None]*(c/c.max())
        out=call(f,a,mask,color,strength)
        floating_array(out,expected,dtype)
        np.testing.assert_array_equal(out[~mask],a[~mask])


def neighbor_oracle(image,known):
    h,w=known.shape
    total=np.zeros(image.shape,np.float64)
    count=np.zeros((h,w),np.int64)
    for y in range(h):
        for x in range(w):
            for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                yy,xx=y+dy,x+dx
                if 0<=yy<h and 0<=xx<w and known[yy,xx]:
                    for c in range(3):
                        total[y,x,c]+=float(image[yy,xx,c])
                    count[y,x]+=1
    return total,count


def spatial_cases():
    rng=np.random.default_rng(184)
    for h,w in [(1,1),(1,5),(5,1),(3,4),(7,8)]:
        for dtype in [np.uint8,np.float64]:
            # Срез с шагом помогает обнаружить предположения о сплошном буфере.
            backing=rng.integers(0,256,(h*2,w*2,3)).astype(dtype)
            if dtype==np.float64: backing=backing/2+.125
            a=backing[::2,::2]
            for known in [np.zeros((h,w),bool),np.ones((h,w),bool),rng.random((h,w))<.5]:
                yield a,known
                yield a[::-1,::-1],known[::-1,::-1]


def test_neighbor_stats(f):
    cases=list(spatial_cases())
    # Известный чёрный пиксель тоже учитывается в количестве соседей.
    cases.append((np.zeros((3,3,3),np.uint8),np.ones((3,3),bool)))
    for a,known in cases:
        expected,count=neighbor_oracle(a,known)
        result=call(f,a,~known)
        assert isinstance(result,tuple) and len(result)==2
        total,number=result
        array(total,expected,np.float64)
        array(number,count)
        assert np.issubdtype(number.dtype,np.integer), 'Количество соседей должно быть целым'


def test_repair_step(f):
    for a,known in spatial_cases():
        missing=~known
        damaged=a.copy(); damaged[missing]=0
        total,count=neighbor_oracle(damaged,known)
        expected=damaged.astype(float)
        remaining=missing.copy()
        for y,x in np.ndindex(missing.shape):
            if missing[y,x] and count[y,x]>0:
                expected[y,x]=total[y,x]/count[y,x]
                remaining[y,x]=False
        result=call(f,damaged,missing)
        assert isinstance(result,tuple) and len(result)==2
        out,mask=result
        array(out,expected,np.float64)
        array(mask,remaining,bool)
        np.testing.assert_array_equal(out[~missing],damaged[~missing],
                                      err_msg='Известные пиксели должны сохраниться точно')
        assert not np.shares_memory(out,damaged)
        assert not np.shares_memory(mask,missing)
    # Один проход не должен использовать значения, вычисленные в этом же проходе.
    a=np.repeat(np.array([[10,0,0,0,50]],np.uint8)[...,None],3,axis=2)
    missing=np.array([[False,True,True,True,False]])
    out,mask=call(f,a,missing)
    array(out[0,:,0],[10,10,0,50,50],np.float64)
    array(mask,[[False,False,True,False,False]],bool)


def test_block_preview(f):
    rng = np.random.default_rng(104)
    for a in [rng.integers(0,256,(5,7,3),dtype=np.uint8),
              np.full((4,4,3),250,np.uint8), rng.integers(0,256,(12,14,3),dtype=np.uint8)[::2,::2]]:
        for k in [1,2,min(a.shape[:2])]:
            h,w = a.shape[:2]
            expected = np.empty((h//k,w//k,3),np.float64)
            for y in range(h//k):
                for x in range(w//k):
                    for channel in range(3):
                        values = [int(a[yy,xx,channel]) for yy in range(y*k,(y+1)*k)
                                  for xx in range(x*k,(x+1)*k)]
                        expected[y,x,channel] = sum(values)/(k*k)
            array(call(f,a,k),expected,np.float64)
        for k in [0,-1,min(a.shape[:2])+1]:
            raises_value_error(f,a,k)


def test_drop_pixels(f):
    for a in images()+[np.zeros((3,5,3),np.uint8)]:
        a[0,0] = 0  # Настоящий чёрный пиксель не означает пропуск.
        for count in sorted({0,1,a.shape[0]*a.shape[1]//2,a.shape[0]*a.shape[1]}):
            for seed in [0,17,42]:
                before_rng = np.random.get_state()
                results = [call(f,a,count,seed),call(f,a,count,seed)]
                after_rng = np.random.get_state()
                assert before_rng[0] == after_rng[0]
                np.testing.assert_array_equal(before_rng[1],after_rng[1], err_msg='Изменён глобальный RNG')
                assert before_rng[2:] == after_rng[2:], 'Изменён глобальный RNG'
                for result in results:
                    assert isinstance(result,tuple) and len(result)==2, 'Верните (damaged, missing)'
                    damaged, mask = result
                    assert isinstance(mask,np.ndarray) and mask.dtype == np.bool_
                    assert mask.shape == a.shape[:2] and int(mask.sum())==count, 'Неверная маска / число потерь'
                    assert isinstance(damaged,np.ndarray) and damaged.dtype == np.uint8 and damaged.shape==a.shape
                    assert not np.shares_memory(damaged,a), 'Изображение должно быть независимой копией'
                    np.testing.assert_array_equal(damaged[~mask],a[~mask])
                    assert np.all(damaged[mask]==0), 'Обнулите все три канала выбранных пикселей'
                for left,right in zip(*results):
                    np.testing.assert_array_equal(left,right,err_msg='Одинаковый seed должен воспроизводить результат')
        for count in [-1,a.shape[0]*a.shape[1]+1]:
            raises_value_error(f,a,count,17)


def restoration_cases():
    rng = np.random.default_rng(106)
    for h,w in [(1,1),(1,5),(5,1),(3,4),(6,7)]:
        a = rng.integers(0,256,(h,w,3),dtype=np.uint8)
        for mode in ['none','one','random','only_one_known']:
            mask = np.zeros((h,w),bool)
            if h*w>1:
                if mode=='one': mask[0,0]=True
                if mode=='random': mask = rng.random((h,w))<.6
                if mode=='only_one_known': mask[:]=True
                mask[-1,-1]=False
            damaged = a.copy()
            damaged[mask]=0
            yield damaged,mask
            yield damaged[::-1,::-1],mask[::-1,::-1]



def test_restoration(f):
    for damaged,mask in restoration_cases():
        result = call(f,damaged,mask)
        validate_restoration(result,damaged,mask)


def test_restore_baseline(f):
    for damaged,mask in restoration_cases():
        expected=damaged.astype(float)
        remaining=mask.copy()
        # Independent oracle: synchronous layers, known pixels remain unchanged.
        for _ in range(mask.size):
            if not remaining.any(): break
            total,count=neighbor_oracle(expected,~remaining)
            fill=remaining & (count>0)
            expected[fill]=total[fill]/count[fill,None]
            remaining[fill]=False
        assert not remaining.any()
        result=call(f,damaged,mask)
        validate_restoration(result,damaged,mask)
        # Проект допускает любой вещественный dtype. Учитываем округление
        # результата в выбранном типе, не ослабляя точное сохранение известных пикселей.
        array(result,expected.astype(result.dtype))


def check_task(name, function, *, verbose=True):
    try:
        if not callable(function):
            raise AssertionError('Функция ещё не определена')
        test = globals().get('test_'+name)
        if name == 'restore_image':
            test = test_restoration
        if test is None:
            raise ValueError('Неизвестная задача: '+name)
        test(function)
    except Exception as error:
        result = {'passed':False, 'message':f'{type(error).__name__}: {error}'}
    else:
        result = {'passed':True, 'message':'Контракт пройден'}
    if verbose:
        print(f"{name}: {result['message']}")
    return result


def report(namespace, *, verbose=True):
    tasks = {name:check_task(name,namespace.get(name),verbose=verbose) for name in TASKS}
    project = {name:check_task(name,namespace.get(name),verbose=verbose)
               for name in ('restore_baseline','restore_image')}
    score = round(sum(TASKS[name] for name,result in tasks.items() if result['passed']),2)
    result = {'mini_score':score,'mini_max':5,'tasks':tasks,'project_contracts':project,
              'manual_review_required':True}
    if verbose:
        print(f'Функциональные проверки №1–11: {score:g}/5. Использование NumPy проверяет ассистент.')
        print('№12–16: до 5 баллов за исследование; прохождение контракта не означает оценку за проект.')
    return result


def test_mean_error(f):
    rng = np.random.default_rng(51)
    backing = rng.uniform(0,255,(8,10))
    for diff in [np.zeros((2,3)), np.array([[0.,30.,90.]]), np.array([[255.]]),
                 backing[::2,::2], backing[::-1,::-1]]:
        selected_view=(rng.random((diff.shape[0]*2,diff.shape[1]*2))<.5)[::2,::2]
        selected_view[0,0]=True
        for selected in [None, np.ones(diff.shape,bool), diff == diff.max(), selected_view]:
            args = (diff,) if selected is None else (diff,selected)
            actual = call(f,*args)
            values = diff.ravel() if selected is None else diff[selected]
            expected = sum(float(x) for x in values)/values.size
            assert isinstance(actual,(float,np.floating))
            np.testing.assert_allclose(actual,expected,rtol=1e-7,atol=1e-8)
        explicit_none = call(f,diff,None)
        assert isinstance(explicit_none,(float,np.floating))
        np.testing.assert_allclose(explicit_none,sum(map(float,diff.flat))/diff.size,
                                   rtol=1e-7,atol=1e-8)
