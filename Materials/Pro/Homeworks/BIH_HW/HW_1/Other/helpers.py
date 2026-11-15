"""Готовые загрузка, показ и измерения. Алгоритмы восстановления пишете вы."""
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
REGIONS = {'background': (.08, .15, .30, .45), 'hat': (.52, .13, .77, .32),
           'body': (.47, .64, .74, .88)}
REGION_NAMES = {'background': 'Фон', 'hat': 'Шапка', 'body': 'Тело утки'}


def load_data(folder=None):
    folder = ROOT if folder is None else Path(folder)
    with Image.open(folder / 'duck_other.png') as image:
        reference = np.array(image.convert('RGB'))
    return reference


def load_final(folder=None):
    folder = ROOT if folder is None else Path(folder)
    with np.load(folder / 'final_photo.npz', allow_pickle=False) as archive:
        return archive['damaged'].copy(), archive['missing'].copy()


def damage(reference, missing):
    result = reference.copy()
    result[missing] = 0
    return result


def region_slices(image, region):
    h, w = image.shape[:2]
    x0, y0, x1, y1 = REGIONS[region]
    return slice(round(y0*h), round(y1*h)), slice(round(x0*w), round(x1*w))


def display_slices(image, region=None, focus=None, padding=4):
    """Один и тот же фрагмент для всех сравниваемых изображений."""
    h, w = image.shape[:2]
    ys, xs = region_slices(image, region) if region else (slice(0, h), slice(0, w))
    if focus is not None:
        points = np.argwhere(focus[ys, xs])
        if len(points):
            y0, x0 = points.min(axis=0)
            y1, x1 = points.max(axis=0) + 1
            ys, xs = (slice(max(ys.start, ys.start + y0 - padding),
                            min(ys.stop, ys.start + y1 + padding)),
                      slice(max(xs.start, xs.start + x0 - padding),
                            min(xs.stop, xs.start + x1 + padding)))
    return ys, xs


def show_images(images, region=None, focus=None):
    """Словарь {подпись: RGB- или серый массив}; region: background, hat, body или None."""
    fig, axes = plt.subplots(1, len(images), figsize=(4*len(images), 3.5),
                             layout='constrained', squeeze=False)
    for ax, (label, array) in zip(axes.flat, images.items()):
        crop = array[display_slices(array, region, focus)]
        shown = np.clip(crop, 0, 255).astype(np.uint8)
        if shown.ndim == 2:
            ax.imshow(shown, cmap='gray', vmin=0, vmax=255, interpolation='nearest')
        else:
            ax.imshow(shown, interpolation='nearest')
        ax.set_title(label)
        ax.axis('off')
    plt.show()
    plt.close(fig)


def show_counts(count, region=None, focus=None):
    """Карта количества соседей с общей целочисленной шкалой от 0 до 4."""
    crop = count[display_slices(count, region, focus)]
    fig, ax = plt.subplots(figsize=(5, 4), layout='constrained')
    shown = ax.imshow(crop, cmap=plt.get_cmap('viridis', 5),
                      vmin=-.5, vmax=4.5, interpolation='nearest')
    ax.set_title('Сколько известных соседей у каждого пикселя')
    ax.axis('off')
    fig.colorbar(shown, ax=ax, ticks=range(5), label='Известных соседей')
    plt.show()
    plt.close(fig)


def make_control_masks(missing, seed=42):
    """Два опыта на известных пикселях снимка; исходные пропуски не оцениваем."""
    h, w = missing.shape
    blocks = np.zeros_like(missing, dtype=bool)
    side = min(16, h, w)
    for ry, rx in [(0.24, 0.18), (0.40, 0.48), (0.75, 0.50)]:
        top, left = min(int(ry*h), h-side), min(int(rx*w), w-side)
        blocks[top:top+side, left:left+side] = ~missing[top:top+side, left:left+side]
    count = int(blocks.sum())
    if count == 0:
        raise ValueError('В выбранных участках нет известных пикселей для проверки')
    positions = np.flatnonzero(~missing)
    points = np.zeros_like(missing, dtype=bool)
    points.flat[np.random.default_rng(seed).choice(positions, count, replace=False)] = True
    return {'points': points, 'blocks': blocks}


def compare_restorations(observed, missing, control, variants, *, error_function, mean_function):
    """Сравнение на контрольных пикселях; серым скрыты все неоцениваемые позиции."""
    # Приближаем нижний квадрат на микрофоне. Для маски отдельных точек – весь снимок.
    h, w = control.shape
    top, left = int(.75*h), int(.50*w)
    box = np.zeros_like(control)
    box[top:min(top+16,h), left:min(left+16,w)] = True
    focus = box if np.count_nonzero(control & box) > 20 else control
    window = display_slices(observed, focus=focus)
    source, selected = observed[window], control[window]
    errors = {name: error_function(source, value[window]) for name, value in variants.items()}
    maximum = max((float(error[selected].max()) for error in errors.values()
                   if selected.any()), default=0.) or 1.
    fig, axes = plt.subplots(2, len(variants)+1,
                             figsize=(3.5*(len(variants)+1), 6.8),
                             layout='constrained', squeeze=False)
    axes[0,0].imshow(source, interpolation='nearest')
    axes[0,0].set_title('До дополнительных потерь')
    axes[1,0].imshow(damage(observed, missing | control)[window], interpolation='nearest')
    axes[1,0].set_title('Вход метода')
    cmap = plt.get_cmap('magma').copy()
    cmap.set_bad('#d9dde3')
    for column, (name, value) in enumerate(variants.items(), 1):
        axes[0,column].imshow(np.clip(value[window],0,255).astype(np.uint8), interpolation='nearest')
        axes[0,column].set_title(name)
        error = errors[name]
        shown = axes[1,column].imshow(np.ma.masked_where(~selected,error), cmap=cmap,
                                      vmin=0, vmax=maximum, interpolation='nearest')
        score = f'{mean_function(error, selected):.3f}' if selected.any() else 'нет контрольных пикселей'
        axes[1,column].set_title('MAE в этом фрагменте: '+score)
    for ax in axes.flat:
        ax.axis('off')
    if variants:
        fig.colorbar(shown, ax=axes[1,1:], shrink=.75, label='Ошибка RGB в контрольном пикселе')
    fig.supxlabel('Светлее – больше ошибка. Серые пиксели не участвуют в оценке.')
    plt.show()
    plt.close(fig)


def validate_restoration(result, damaged, missing):
    assert isinstance(result, np.ndarray), 'Верните ndarray'
    assert result.shape == damaged.shape, 'Форма результата должна совпадать с изображением'
    assert np.issubdtype(result.dtype, np.floating), 'Результат должен быть вещественным массивом'
    assert np.isfinite(result).all(), 'В результате есть NaN или бесконечности'
    assert ((result >= 0) & (result <= 255)).all(), 'Цвета должны лежать в [0, 255]'
    assert not np.shares_memory(result, damaged), 'Нужен независимый результат'
    np.testing.assert_array_equal(result[~missing], damaged[~missing],
                                  err_msg='Известные пиксели изменились')


def preview_experiment(function, photo, *, error_function, mean_function):
    """Общая область и одинаковое разрешение для честного сравнения способов."""
    from IPython.display import HTML, display
    h,w=photo.shape[:2]
    original=photo[:h//16*16,:w//16*16]
    fig,axes=plt.subplots(2,3,figsize=(12,6),layout='constrained')
    records=[]
    for column,k in enumerate([4,8,16]):
        averaged=np.rint(function(original,k)).clip(0,255).astype(np.uint8)
        sparse=original[::k,::k].copy()
        for row,(label,small) in enumerate([('Каждый k-й',sparse),('Среднее блока',averaged)]):
            expanded=np.repeat(np.repeat(small,k,axis=0),k,axis=1)
            error=mean_function(error_function(original, expanded))
            axes[row,column].imshow(expanded,interpolation='nearest')
            axes[row,column].set_title(f'{label}, k={k}\n{small.nbytes / 1024:.1f} КиБ; MAE={error:.2f}')
            axes[row,column].axis('off')
            records.append(f'<tr><td>{label}</td><td>{k}</td><td>{small.shape}</td><td>{small.nbytes}</td><td>{error:.3f}</td></tr>')
    plt.show();plt.close(fig)
    display(HTML('<table><tr><th>Способ</th><th>factor</th><th>Форма</th><th>Байты uint8</th><th>MAE</th></tr>'+''.join(records)+'</table>'))


def show_error_map(diff, selected=None):
    shown = diff if selected is None else np.ma.masked_where(~selected, diff)
    cmap = plt.get_cmap('magma').copy()
    cmap.set_bad('#d9dde3')
    fig, ax = plt.subplots(figsize=(9,5), layout='constrained')
    maximum = float(diff.max() if selected is None else diff[selected].max()) or 1.
    plot = ax.imshow(shown, cmap=cmap, vmin=0, vmax=maximum, interpolation='nearest')
    ax.set_title('Карта абсолютных ошибок RGB')
    ax.axis('off')
    fig.colorbar(plot, ax=ax, label='Средняя абсолютная ошибка RGB в пикселе')
    plt.show()
    plt.close(fig)
