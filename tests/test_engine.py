from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pytest
from PIL import Image
from search.engine import SearchConfig, SearchIndex, histogram, feature_matrix, fingerprint, HISTOGRAM_METRICS, VECTOR_METRICS
from search.images import read_rgb, discover
from utils.download_dataset import extract_photos, prepare


def pixels(colour):
    return np.full((12, 12, 3), colour, dtype=np.uint8)


@pytest.mark.parametrize('space', ['HSV', 'RGB'])
@pytest.mark.parametrize('bins', [4, 8])
def test_histograms(space, bins):
    feature = histogram(pixels((240, 20, 40)), space, bins)
    assert feature.shape == (bins ** 3,)
    assert feature.sum() == pytest.approx(1)
    assert (feature >= 0).all()


@pytest.mark.parametrize('pca,metric', [(False, m) for m in HISTOGRAM_METRICS] + [(True, m) for m in VECTOR_METRICS])
def test_ranking(pca, metric):
    rng = np.random.default_rng(13)
    matrix = rng.dirichlet(np.ones(64), size=12)
    index = SearchIndex([f'{i:02}' for i in range(12)], matrix, SearchConfig(bins=4, pca=pca, metric=metric))
    results = index.rank(matrix[3], 20)
    assert results[0][0] == '03'
    assert all(np.isfinite(d) and d >= -1e-10 for _, d in results)
    assert '03' not in dict(index.rank(matrix[3], 20, '03'))
    if pca:
        np.testing.assert_allclose(index.transform(matrix[3]), index.features[3], atol=1e-12)
        assert index.pca.explained_variance_ratio_.sum() >= .95


def test_ties_and_empty():
    matrix = np.ones((3, 64)) / 64
    index = SearchIndex(['z', 'a', 'b'], matrix, SearchConfig(bins=4))
    assert [n for n, _ in index.rank(matrix[0])] == ['a', 'b', 'z']
    assert index.rank(matrix[0], 0) == []
    with pytest.raises(ValueError):
        SearchConfig(pca=True)
    with pytest.raises(ValueError):
        SearchIndex(['a'], matrix[:1], SearchConfig(bins=4))
    with pytest.raises(ValueError):
        SearchIndex(['a', 'b', 'c'], matrix, SearchConfig(bins=4, pca=True, metric='L2'))


def test_uploads_and_masks(tmp_path):
    with pytest.raises(ValueError):
        read_rgb(b'not an image')
    with pytest.raises(ValueError):
        read_rgb(b'x' * (10 * 1024 * 1024 + 1))
    with pytest.raises(ValueError):
        buffer = BytesIO()
        Image.new('1', (5000, 5000)).save(buffer, format='PNG')
        read_rgb(buffer.getvalue())
    buffer = BytesIO()
    Image.new('RGBA', (5, 5), (0, 0, 0, 0)).save(buffer, format='PNG')
    assert read_rgb(buffer.getvalue()).min() == 255
    Image.new('RGB', (10, 10), 'red').save(tmp_path / 'a.bmp')
    Image.new('RGB', (10, 10), 'white').save(tmp_path / 'a_GT.bmp')
    (tmp_path / 'bad.png').write_bytes(b'bad')
    paths, skipped = discover(tmp_path)
    assert [p.name for p in paths] == ['a.bmp']
    assert skipped == ['bad.png']


def test_cache_rebuild(tmp_path):
    paths = []
    for i, colour in enumerate(['red', 'blue']):
        path = tmp_path / f'{i}.png'
        Image.new('RGB', (5, 5), colour).save(path)
        paths.append(path)
    signature = fingerprint(paths)
    original = feature_matrix(paths, 'RGB', 4, tmp_path / 'cache', signature)
    np.testing.assert_array_equal(original, feature_matrix(paths, 'RGB', 4, tmp_path / 'cache', signature))
    next((tmp_path / 'cache').iterdir()).write_bytes(b'broken')
    np.testing.assert_array_equal(original, feature_matrix(paths, 'RGB', 4, tmp_path / 'cache', signature))
    Image.new('RGB', (5, 5), 'green').save(paths[0])
    assert fingerprint(paths) != signature


def test_archive_safety_and_incomplete(tmp_path):
    archive = tmp_path / 'bad.zip'
    with ZipFile(archive, 'w') as bundle:
        bundle.writestr('../escape.png', b'bad')
    with pytest.raises(ValueError, match='unsafe'):
        extract_photos(archive, tmp_path)
    with ZipFile(archive, 'w') as bundle:
        buffer = BytesIO()
        Image.new('RGB', (10, 10), 'red').save(buffer, format='BMP')
        bundle.writestr('nested/Images/a.bmp', buffer.getvalue())
        bundle.writestr('nested/Images/a_GT.bmp', buffer.getvalue())
    dest = tmp_path / 'extract'
    dest.mkdir()
    extract_photos(archive, dest)
    assert [p.name for p in dest.iterdir()] == ['a.bmp']
    with pytest.raises(ValueError, match='Expected 591'):
        prepare(tmp_path / 'data', archive)
    assert not (tmp_path / 'data/MSRC_ObjCategImageDatabase_v2/Images').exists()


def test_preparation_failure_preserves_data(tmp_path, monkeypatch):
    import utils.download_dataset as setup
    existing = tmp_path / 'MSRC_ObjCategImageDatabase_v2/Images'
    existing.mkdir(parents=True)
    Image.new('RGB', (10, 10), 'red').save(existing / 'old.bmp')
    def offline(*args):
        raise OSError('offline')
    monkeypatch.setattr(setup, 'download', offline)
    with pytest.raises(OSError, match='offline'):
        setup.prepare(tmp_path)
    assert (existing / 'old.bmp').exists()


def test_preparation_is_offline_when_complete(tmp_path, monkeypatch):
    import utils.download_dataset as setup
    existing = tmp_path / 'MSRC_ObjCategImageDatabase_v2/Images'
    existing.mkdir(parents=True)
    for i, colour in enumerate(('red', 'blue')):
        Image.new('RGB', (10, 10), colour).save(existing / f'{i}.bmp')
    monkeypatch.setattr(setup, 'EXPECTED_IMAGES', 2)
    monkeypatch.setattr(setup, 'download', lambda *args: pytest.fail('Unexpected network access'))
    setup.prepare(tmp_path)
    assert len(list((tmp_path / 'cache').glob('*.npz'))) == 4


def test_unlabelled_segmentation_is_not_extracted(tmp_path):
    archive = tmp_path / 'dataset.zip'
    buffer = BytesIO()
    Image.new('RGB', (10, 10), 'red').save(buffer, format='BMP')
    with ZipFile(archive, 'w') as bundle:
        bundle.writestr('dataset/Images/a.bmp', buffer.getvalue())
        bundle.writestr('dataset/SegmentationsGTHighQuality/a.bmp', buffer.getvalue())
    extract_photos(archive, tmp_path)
    assert (tmp_path / 'a.bmp').exists()
