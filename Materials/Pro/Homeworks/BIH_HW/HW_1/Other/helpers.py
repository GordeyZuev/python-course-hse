"""Готовые загрузка, показ и измерения. Алгоритмы восстановления пишете вы."""
from pathlib import Path
import csv
import time
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
REGIONS = {'background': (.08, .15, .30, .45), 'hat': (.52, .13, .77, .32),
           'body': (.47, .64, .74, .88)}
REGION_NAMES = {'background': 'Фон', 'hat': 'Шапка', 'body': 'Тело утки'}
REQUIRED_CASES = ('random_30_seed42', 'blocks_16', 'matched_random_16')
FIELDS = ('method', 'case', 'parameters', 'missing_pixels', 'missing_fraction',
          'mae_missing', 'mae_background', 'mae_hat', 'mae_body', 'seconds')


def load_data(folder=None):
    folder = ROOT if folder is None else Path(folder)
    with Image.open(folder / 'duck_other.png') as image:
        reference = np.array(image.convert('RGB'))
    with np.load(folder / 'masks.npz', allow_pickle=False) as archive:
        masks = {name: archive[name].copy() for name in archive.files}
    return reference, masks


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


def compare_restorations(reference, missing, variants, region='hat', *, error_function=None):
    """Результаты рядом; ниже – ошибки RGB с одной шкалой для всех вариантов."""
    window = display_slices(reference, region, missing)
    original, selected = reference[window], missing[window]
    errors = {name: (np.abs(value[window].astype(float) - original.astype(float)).mean(axis=2)
                     if error_function is None else error_function(original, value[window]))
              for name, value in variants.items()}
    maximum = max((float(error[selected].max()) for error in errors.values()
                   if selected.any()), default=0.) or 1.
    fig, axes = plt.subplots(2, len(variants) + 1,
                             figsize=(3.5*(len(variants)+1), 6.8),
                             layout='constrained', squeeze=False)
    axes[0, 0].imshow(original, interpolation='nearest')
    axes[0, 0].set_title('Оригинал')
    axes[1, 0].imshow(damage(original, selected), interpolation='nearest')
    axes[1, 0].set_title('Повреждение')
    cmap = plt.get_cmap('magma').copy()
    cmap.set_bad('#d9dde3')
    for column, (name, value) in enumerate(variants.items(), 1):
        axes[0, column].imshow(np.clip(value[window], 0, 255).astype(np.uint8), interpolation='nearest')
        axes[0, column].set_title(name)
        error = errors[name]
        shown = axes[1, column].imshow(np.ma.masked_where(~selected, error),
                                       cmap=cmap, vmin=0, vmax=maximum, interpolation='nearest')
        score = f'{error[selected].mean():.3f}' if selected.any() else 'нет потерь'
        axes[1, column].set_title('MAE в этом фрагменте: ' + score)
    for ax in axes.flat:
        ax.axis('off')
    if variants:
        fig.colorbar(shown, ax=axes[1, 1:], shrink=.75, label='Ошибка RGB в пикселе')
    fig.supxlabel('Внизу: светлее – больше ошибка; серым показаны известные пиксели.')
    plt.show()
    plt.close(fig)


def show_results(rows):
    """Показывает журнал компактной таблицей, не меняя исходные записи."""
    from html import escape
    from IPython.display import HTML, display
    columns = (('method', 'Метод'), ('case', 'Повреждение'),
               ('parameters', 'Параметры'), ('mae_missing', 'MAE'),
               ('mae_background', 'Фон'), ('mae_hat', 'Шапка'), ('mae_body', 'Тело утки'))
    header = ''.join('<th>' + label + '</th>' for _, label in columns)
    body = []
    for row in rows:
        cells = []
        for key, _ in columns:
            value = row[key]
            text = '–' if value is None else f'{value:.3f}' if key.startswith('mae_') else str(value)
            cells.append('<td>' + escape(text) + '</td>')
        body.append('<tr>' + ''.join(cells) + '</tr>')
    display(HTML('<table><thead><tr>' + header + '</tr></thead><tbody>'
                 + ''.join(body) + '</tbody></table>'))


def validate_restoration(result, damaged, missing):
    assert isinstance(result, np.ndarray), 'Верните ndarray'
    assert result.shape == damaged.shape, 'Форма результата должна совпадать с изображением'
    assert np.issubdtype(result.dtype, np.floating), 'Результат должен быть вещественным массивом'
    assert np.isfinite(result).all(), 'В результате есть NaN или бесконечности'
    assert ((result >= 0) & (result <= 255)).all(), 'Цвета должны лежать в [0, 255]'
    assert not np.shares_memory(result, damaged), 'Нужен независимый результат'
    np.testing.assert_array_equal(result[~missing], damaged[~missing],
                                  err_msg='Известные пиксели изменились')


def measure(reference, restored, missing, error_function=None):
    """MAE только по потерянным пикселям и всем трём каналам; None, если их нет."""
    delta = (np.abs(restored.astype(np.float64) - reference.astype(np.float64)).mean(axis=2)
             if error_function is None else error_function(reference, restored))
    scores = {'mae_missing': float(delta[missing].mean()) if missing.any() else None}
    for region in REGIONS:
        slices = region_slices(reference, region)
        selected = missing[slices]
        scores['mae_' + region] = (float(delta[slices][selected].mean())
                                   if selected.any() else None)
    return scores


def evaluate(method, reference, missing, *, name, case, parameters=None, error_function=None):
    """Возвращает (результат, строка журнала). Оригинал не передаётся в method."""
    import json
    parameters = {} if parameters is None else dict(parameters)
    damaged = damage(reference, missing)
    before, mask_before = damaged.copy(), missing.copy()
    start = time.perf_counter()
    result = method(damaged, missing, **parameters)
    elapsed = time.perf_counter() - start
    np.testing.assert_array_equal(damaged, before, err_msg='Изменён входной массив')
    np.testing.assert_array_equal(missing, mask_before, err_msg='Изменена маска')
    validate_restoration(result, damaged, missing)
    row = {'method': name, 'case': case,
           'parameters': json.dumps(parameters, sort_keys=True, ensure_ascii=False),
           'missing_pixels': int(missing.sum()), 'missing_fraction': float(missing.mean()),
           **measure(reference, result, missing, error_function), 'seconds': elapsed}
    return result, row


def save_results(rows, path='results.csv'):
    """Сохраняет текущий журнал заново, без накопления дубликатов между запусками."""
    with Path(path).open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

def preview_experiment(function, photo):
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
            error=float(np.abs(expanded.astype(float)-original.astype(float)).mean())
            axes[row,column].imshow(expanded,interpolation='nearest')
            axes[row,column].set_title(f'{label}, k={k}\n{small.nbytes / 1024:.1f} КиБ; MAE={error:.2f}')
            axes[row,column].axis('off')
            records.append(f'<tr><td>{label}</td><td>{k}</td><td>{small.shape}</td><td>{small.nbytes}</td><td>{error:.3f}</td></tr>')
    plt.show();plt.close(fig)
    display(HTML('<table><tr><th>Способ</th><th>factor</th><th>Форма</th><th>Байты uint8</th><th>MAE</th></tr>'+''.join(records)+'</table>'))
