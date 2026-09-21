"""Prepare MSRC-v2 once. Supports an upstream download or a local archive."""
import argparse
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
import time
from urllib.request import urlopen
from zipfile import ZipFile, BadZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from search.images import discover, is_photo, read_rgb
from search.engine import feature_matrix, fingerprint
from utils.paths import DATA

FILE_URL = 'https://download.microsoft.com/download/3/3/9/339D8A24-47D7-412F-A1E8-1A415BC48A15/msrc_objcategimagedatabase_v2.zip'
MAX_ARCHIVE = 256 * 1024 * 1024
MAX_EXPANDED = 512 * 1024 * 1024
EXPECTED_IMAGES = 591


def download(url, target):
    deadline = time.monotonic() + 180
    with urlopen(url, timeout=30) as response, target.open('wb') as output:
        total = 0
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_ARCHIVE or time.monotonic() > deadline:
                raise ValueError('Dataset download exceeded its size or time limit.')
            output.write(chunk)


def extract_photos(archive, destination):
    with ZipFile(archive) as bundle:
        members = bundle.infolist()
        if len(members) > 10000 or sum(m.file_size for m in members) > MAX_EXPANDED:
            raise ValueError('Archive is too large.')
        names = set()
        for member in members:
            path = PurePosixPath(member.filename.replace('\\', '/'))
            if path.is_absolute() or '..' in path.parts or ':' in member.filename:
                raise ValueError('Archive contains an unsafe path.')
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Archive contains a symbolic link.')
            if member.is_dir() or 'Images' not in path.parts[:-1] or not is_photo(Path(path.name)):
                continue
            if member.file_size > 10 * 1024 * 1024 or path.name in names:
                raise ValueError('Archive contains oversized or duplicate images.')
            names.add(path.name)
            target = destination / path.name
            with bundle.open(member) as source, target.open('wb') as output:
                shutil.copyfileobj(source, output)
            read_rgb(target)


def prepare(data_root: Path, archive: Path | None = None):
    target = data_root / 'MSRC_ObjCategImageDatabase_v2' / 'Images'
    paths, skipped = discover(target)
    if len(paths) != EXPECTED_IMAGES or skipped:
        data_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=data_root) as work:
            work = Path(work)
            source = archive
            if source is None:
                source = work / 'dataset.zip'
                download(FILE_URL, source)
            if source.stat().st_size > MAX_ARCHIVE:
                raise ValueError('Archive exceeds 256 MB.')
            staged = work / 'Images'
            staged.mkdir()
            extract_photos(source, staged)
            paths, skipped = discover(staged)
            if len(paths) != EXPECTED_IMAGES or skipped:
                raise ValueError(f'Expected {EXPECTED_IMAGES} readable photos, found {len(paths)}. Existing data was not changed.')
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                backup = work / 'previous-images'
                target.rename(backup)
                try:
                    staged.rename(target)
                except OSError:
                    backup.rename(target)
                    raise
            else:
                staged.rename(target)
    paths, _ = discover(target)
    signature = fingerprint(paths)
    for space in ('RGB', 'HSV'):
        for bins in (4, 8):
            feature_matrix(paths, space, bins, data_root / 'cache', signature)
    print(f'Ready: {len(paths)} photos and four cached feature matrices in {data_root}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Local MSRC-v2 ZIP, used without network access')
    parser.add_argument('--data-dir', type=Path, default=DATA)
    args = parser.parse_args()
    try:
        prepare(args.data_dir, args.archive)
    except (OSError, ValueError, BadZipFile) as exc:
        parser.exit(1, f'Preparation failed: {exc}\nTry --archive /path/to/msrc.zip.\n')


if __name__ == '__main__':
    main()
