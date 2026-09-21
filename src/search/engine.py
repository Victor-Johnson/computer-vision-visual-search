"""Numerical retrieval, independent of Streamlit and legacy pickle artifacts."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import tempfile
import cv2
import numpy as np
from sklearn.decomposition import PCA
from .images import read_rgb

VECTOR_METRICS = ('L1', 'L2', 'Cosine', 'Mahalanobis')
HISTOGRAM_METRICS = ('Bhattacharyya', 'Chi-Square') + VECTOR_METRICS


@dataclass(frozen=True)
class SearchConfig:
    space: str = 'HSV'
    bins: int = 8
    pca: bool = False
    metric: str = 'Bhattacharyya'

    def __post_init__(self):
        if self.space not in ('RGB', 'HSV') or self.bins not in (4, 8):
            raise ValueError('Use RGB or HSV with 4 or 8 bins per channel.')
        if self.metric not in (VECTOR_METRICS if self.pca else HISTOGRAM_METRICS):
            raise ValueError('This distance is not compatible with the selected representation.')


def histogram(rgb: np.ndarray, space='HSV', bins=8) -> np.ndarray:
    if space not in ('RGB', 'HSV') or bins not in (4, 8):
        raise ValueError('Unsupported histogram configuration.')
    pixels = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV) if space == 'HSV' else rgb
    ranges = [0, 180, 0, 256, 0, 256] if space == 'HSV' else [0, 256] * 3
    hist = cv2.calcHist([pixels], [0, 1, 2], None, [bins] * 3, ranges).ravel().astype(float)
    return hist / max(hist.sum(), 1)


def fingerprint(paths: list[Path]) -> str:
    # Include content so replacement images invalidate cached features on restart.
    digest = hashlib.sha256(b'rgb-thumbnail-1024-hist-v1')
    for path in paths:
        digest.update(str(path).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:24]


def feature_matrix(paths, space, bins, cache_dir: Path, signature: str):
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / f'{signature}-{space}-{bins}.npz'
    try:
        with np.load(target, allow_pickle=False) as data:
            matrix = data['features']
        if matrix.shape == (len(paths), bins ** 3) and np.isfinite(matrix).all():
            return matrix
    except (OSError, ValueError, KeyError):
        pass
    matrix = np.stack([histogram(read_rgb(p), space, bins) for p in paths])
    with tempfile.NamedTemporaryFile(dir=cache_dir, suffix='.npz', delete=False) as temp:
        temporary = Path(temp.name)
    try:
        np.savez_compressed(temporary, features=matrix)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return matrix


class SearchIndex:
    def __init__(self, names, features, config: SearchConfig):
        self.names = tuple(names)
        self.config = config
        self.pca = None
        self.inverse_covariance = None
        self.features = np.asarray(features, dtype=float)
        if len(self.features) < 2:
            raise ValueError('At least two readable dataset images are required.')
        if config.pca:
            if np.sum(np.var(self.features, axis=0)) < 1e-15:
                raise ValueError('PCA needs a dataset with some colour variation.')
            self.pca = PCA(n_components=0.95, svd_solver='full')
            self.features = self.pca.fit_transform(self.features)
        if config.metric == 'Mahalanobis':
            covariance = np.atleast_2d(np.cov(self.features, rowvar=False))
            self.inverse_covariance = np.linalg.inv(covariance + np.eye(covariance.shape[0]) * 1e-6)

    def transform(self, feature):
        if self.pca is None:
            return feature
        # Explicit contraction avoids platform BLAS warnings on one-row inputs.
        return np.einsum('ij,j->i', self.pca.components_, feature - self.pca.mean_)

    def rank(self, feature, top_k=10, exclude=None):
        query = self.transform(feature)
        matrix = self.features
        delta = matrix - query
        metric = self.config.metric
        if metric == 'L1':
            distances = np.abs(delta).sum(axis=1)
        elif metric == 'L2':
            distances = np.linalg.norm(delta, axis=1)
        elif metric == 'Cosine':
            norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query)
            similarity = np.divide(matrix @ query, norms, out=np.zeros(len(matrix)), where=norms > 1e-15)
            distances = 1 - np.clip(similarity, -1, 1)
            distances[(np.linalg.norm(matrix, axis=1) < 1e-15) & (np.linalg.norm(query) < 1e-15)] = 0
        elif metric == 'Chi-Square':
            distances = 0.5 * np.sum(delta ** 2 / (matrix + query + 1e-12), axis=1)
        elif metric == 'Bhattacharyya':
            distances = -np.log(np.clip(np.sqrt(matrix * query).sum(axis=1), 1e-12, 1))
        else:
            distances = np.sqrt(np.maximum(np.einsum('ij,jk,ik->i', delta, self.inverse_covariance, delta), 0))
        results = [(name, float(distance)) for name, distance in zip(self.names, distances)
                   if name != exclude and np.isfinite(distance)]
        return sorted(results, key=lambda item: (item[1], item[0]))[:max(0, top_k)]
