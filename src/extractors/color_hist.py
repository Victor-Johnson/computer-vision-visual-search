"""
Color Histogram Function this is a util function in the extractor to get the 
Color Histogram
"""

import cv2
from dataclasses import dataclass
import numpy as np
from typing import Tuple 


@dataclass(frozen=True)

class ColorHistConfig:
    space : str = "HSV"
    bins : Tuple[int,int,int] = (8,8,8)
    normalize : bool = True


def convert_space(img_bgr:np.ndarray,space:str)-> np.ndarray:
    """
    Converts an image from BGR  default) to another colour space.

    Parameters
    ----------
    img_bgr : np.ndarray
        The input image read by OpenCV (BGR order).
    space : str
        Target colour space: 'HSV' or 'RGB'.

    Returns
    -------
    np.ndarray
        The converted image.
    """
    if space.upper() == "RGB":
        return cv2.cvtColor(img_bgr,cv2.COLOR_BGR2RGB)
    if space.upper() == "HSV":
        return cv2.cvtColor(img_bgr,cv2.COLOR_BGR2HSV)
    raise ValueError(f"The Image Color space is unsupported : {space}\n")
    

def color_histogram(img_br:np.ndarray,cfg : ColorHistConfig)-> np.ndarray:
    """
    Computes a global colour histogram for the given image.

    Parameters
    ----------
    img_bgr : np.ndarray
        Input image (BGR format).
    cfg : ColorHistConfig
        Configuration defining colour space, bins, and normalization.

    Returns
    -------
    np.ndarray
        Flattened, optionally normalized colour histogram.
    """

    img = convert_space(img_br,cfg.space)
    ranges = ((0,180),(0,256),(0,256)) if cfg.space.upper() == "HSV" else ((0,256),)*3
    hist = cv2.calcHist([img],[0,1,2] , None ,cfg.bins, [r for pair in ranges for r in pair])
    hist = hist.astype(np.float32)
    if cfg.normalize:
        s = hist.sum()
        if s>0:
            hist /=s
    
    return hist.flatten()

