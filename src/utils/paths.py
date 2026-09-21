"""Paths shared by notebooks and the deployable application; imports do not write files."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get('VISUAL_SEARCH_DATA', ROOT / 'data'))
IMAGES = DATA / 'MSRC_ObjCategImageDatabase_v2' / 'Images'
CACHE = DATA / 'cache'
DESCRIPTORS = DATA / 'Descriptors'
REPORT = ROOT / 'report'
