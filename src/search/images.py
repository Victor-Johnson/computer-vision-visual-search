"""Image ingestion. Every public image array is RGB uint8."""
from io import BytesIO
from pathlib import Path
import warnings
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 20_000_000
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}


def is_photo(path: Path) -> bool:
    return path.suffix.lower() in EXTENSIONS and not any(
        marker in path.stem.upper() for marker in ('_GT', '_GTORIG', '_MASK'))


def read_rgb(source: Path | bytes) -> np.ndarray:
    if isinstance(source, bytes) and len(source) > MAX_BYTES:
        raise ValueError('Please choose an image smaller than 10 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(source) if isinstance(source, bytes) else source) as image:
                if image.width * image.height > MAX_PIXELS:
                    raise ValueError('Please choose an image with at most 20 million pixels.')
                image = ImageOps.exif_transpose(image)
                if image.mode in ('RGBA', 'LA') or 'transparency' in image.info:
                    rgba = image.convert('RGBA')
                    background = Image.new('RGBA', rgba.size, 'white')
                    image = Image.alpha_composite(background, rgba)
                image = image.convert('RGB')
                image.thumbnail((1024, 1024))
                return np.asarray(image).copy()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValueError('This file could not be read. Try a JPG, PNG, or BMP image.') from exc


def discover(root: Path) -> tuple[list[Path], list[str]]:
    valid, skipped = [], []
    for path in sorted(root.rglob('*')):
        if path.is_file() and is_photo(path):
            try:
                read_rgb(path)
                valid.append(path)
            except ValueError:
                skipped.append(path.name)
    return valid, skipped
