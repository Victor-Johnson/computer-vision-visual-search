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

echo "--------------------------------------------------------"
echo "Computer Vision Coursework - Visual Search Project"
echo "--------------------------------------------------------"

# Check environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.9+."
    exit 1
fi

# Create virtual environment if missing
if [ ! -d "$ROOT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source "$ROOT_DIR/venv/bin/activate"

# Install dependencies
echo "Installing requirements..."
pip install --quiet numpy opencv-python matplotlib scikit-learn streamlit tqdm

# Check dataset and descriptors
if [ ! -d "$DATA_DIR" ]; then
    echo "⚠️ Dataset directory not found: $DATA_DIR"
    echo "Please download the MSRC dataset before running."
    exit 1
fi

if [ ! -f "$DESC_FILE" ]; then
    echo "⚠️ Descriptor file missing. Please run PCA extraction notebook first."
    exit 1
fi

# Run based on argument
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


#### bash run_project.sh notebook
#### bash run_project.sh app
