#%% md
### This script downloads and unzips the MSRC-v2 dataset for the Visual Image Search.
#%%

from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO
from pathlib import Path

#%%
# URL for the MSRC-v2 dataset
FILE_URL = "http://download.microsoft.com/download/3/3/9/339D8A24-47D7-412F-A1E8-1A415BC48A15/msrc_objcategimagedatabase_v2.zip"

#%%
def download_and_unzip(url: str, extract_to: str = "data/Images") -> None:
    """
    Downloads a ZIP file from `url` and extracts it into `extract_to`.
    """
    Path(extract_to).mkdir(parents=True, exist_ok=True)     # ensure target folder exists

    print(f"Downloading from {url} ...")
    with urlopen(url) as response:
        with ZipFile(BytesIO(response.read())) as zf:
            print(f"Extracting to {extract_to} ...")
            zf.extractall(path=extract_to)
    print("✅ Download and extraction complete!")

#%%
if __name__ == "__main__":
    download_and_unzip(FILE_URL, "/home/sally/Desktop/coursework/CV/computer-vision-visual-search/data")

# %%
