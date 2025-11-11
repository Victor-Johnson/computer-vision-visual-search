#!/bin/bash
# --------------------------------------------------------
#  Computer Vision Coursework – Auto Runner
#  Author: Victor Johnson (University of Surrey, 2025)
# --------------------------------------------------------

ROOT_DIR="$(dirname "$(realpath "$0")")"
DATA_DIR="$ROOT_DIR/data/MSRC_ObjCategImageDatabase_v2/Images"
DESC_FILE="$ROOT_DIR/data/Descriptors/HSV_PCA_SAFE.pkl"
NOTEBOOK="$ROOT_DIR/notebooks/02_Image_Retrieval_Fallback.ipynb"
APP_FILE="$ROOT_DIR/src/streamlit_app.py"
REQ_FILE="$ROOT_DIR/requirements.txt"

echo "--------------------------------------------------------"
echo "Computer Vision Coursework - Visual Search Project"
echo "--------------------------------------------------------"

# --------------------------------------------------------
# 1. Check Python installation
# --------------------------------------------------------
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.9+."
    exit 1
fi

# --------------------------------------------------------
# 2. Create virtual environment if not present
# --------------------------------------------------------
if [ ! -d "$ROOT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$ROOT_DIR/venv"
fi

source "$ROOT_DIR/venv/bin/activate"

# --------------------------------------------------------
# 3. Install dependencies from requirements.txt
# --------------------------------------------------------
if [ -f "$REQ_FILE" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install --quiet -r "$REQ_FILE"
else
    echo "requirements.txt not found. Installing core packages..."
    pip install --quiet numpy opencv-python matplotlib scikit-learn streamlit tqdm jupyter
fi

# --------------------------------------------------------
# 4. Download dataset if missing
# --------------------------------------------------------
if [ ! -d "$DATA_DIR" ]; then
    echo "Dataset not found. Downloading MSRC dataset..."
    mkdir -p "$ROOT_DIR/data"
    cd "$ROOT_DIR/data" || exit 1

    # The original Microsoft URL:
    ZIP_URL="http://download.microsoft.com/download/3/3/9/339D8A24-47D7-412F-A1E8-1A415BC48A15/msrc_objcategimagedatabase_v2.zip"

    wget -q "$ZIP_URL" -O msrc_dataset.zip
    echo "Unzipping dataset..."
    unzip -q msrc_dataset.zip -d "$ROOT_DIR/data/MSRC_ObjCategImageDatabase_v2"
    rm msrc_dataset.zip
    echo "✅ Dataset downloaded and extracted."
    cd "$ROOT_DIR" || exit 1
fi

# --------------------------------------------------------
# 5. Verify descriptor file
# --------------------------------------------------------
if [ ! -f "$DESC_FILE" ]; then
    echo "⚠️ Descriptor file missing. Please run the PCA extraction notebook first."
    echo "Run the notebook using: bash run_project.sh notebook"
    deactivate
    exit 1
fi

# --------------------------------------------------------
# 6. Run mode selector
# --------------------------------------------------------
case "$1" in
    notebook)
        echo "Launching Jupyter Notebook..."
        jupyter notebook "$NOTEBOOK"
        ;;
    app)
        echo "Launching Streamlit App..."
        streamlit run "$APP_FILE"
        ;;
    *)
        echo "Usage: bash run_project.sh [notebook | app]"
        ;;
esac

deactivate
