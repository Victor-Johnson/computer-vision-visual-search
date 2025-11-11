from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
IMAGES = DATA / "MSRC_ObjCategImageDatabase_v2" / "Images"
DESCRIPTORS = DATA / "Descriptors"
REPORT = ROOT / "report"

# Auto-create folders if missing
for d in [DESCRIPTORS, REPORT]:
    d.mkdir(parents=True, exist_ok=True)
