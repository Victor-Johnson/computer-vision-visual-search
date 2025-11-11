# utils.py script to list images 
# This utility file was built to give a clean resuable way to get all images from the MSRC dataset

from pathlib import Path
from typing import List, Set, Union

def list_images(root: Union[str, Path], exts: Set[str] = {".jpg", ".jpeg", ".png", ".bmp"}) -> List[Path]:
    """
    Recursively list image files in a directory.

    Parameters
    ----------
    root : str | Path
        The root directory containing images.
    exts : set of str
        Allowed image file extensions.

    Returns
    -------
    list of Path
        List of image file paths.
    """
    dir_root = Path(root)
    if not dir_root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")
    paths = [p for p in dir_root.rglob("*") if p.suffix.lower() in exts]
    if len(paths) == 0:
        print(f"⚠️ No images found in directory {root}")
    return paths
