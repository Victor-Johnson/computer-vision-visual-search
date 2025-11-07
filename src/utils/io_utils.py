# utils.py script to list images 
# This utility file was built to give a clean resuable way to get all images from the MSRC dataset


from pathlib import Path
from typing import List ,Set 


def list_images(root:str | Path , exts:Set[str]=
                {".jpg",".jpeg",".png",".bmp"}) ->  List[Path]:
    """
    List[Path]:
    List all image files in the given root directory and its subdirectories.

    Args:
        root (str | Path): The root directory to search for image files.
        exts (Set[str], optional): A set of file extensions to consider as images.
                                   Defaults to {".jpg", ".jpeg", ".png", ".bmp"}.

    Returns
    -------
    list of Path
        List of image file paths.
    """
    dir_root = Path(root)
    if not dir_root.exists():
        raise FileNotFoundError(f"Directory not found :{root}")
    paths = [p for p in dir_root.rglob("*") if p.suffix.lower() in exts]
    if len(paths) == 0:
        print("No Images Found in this dir {root}")
   return paths

        

     