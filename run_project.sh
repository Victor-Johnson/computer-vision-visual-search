#!/bin/bash
# --------------------------------------------------------
#  Computer Vision Coursework – Auto Runner (macOS & Linux)
#  Author: Victor Johnson (University of Surrey, 2025)
# --------------------------------------------------------

set -e  # Exit immediately if any command fails

ROOT_DIR="$(dirname "$(realpath "$0")")"
DATA_DIR="$ROOT_DIR/data/MSRC_ObjCategImageDatabase_v2/Images"
DESC_FILE="$ROOT_DIR/data/Descriptors/HSV_PCA_SAFE.pkl"
NOTEBOOK="$ROOT_DIR/notebooks/02_Image_Retrieval_Fallback.ipynb"
APP_FILE="$ROOT_DIR/src/streamlit-app.py"
REQ_FILE="$ROOT_DIR/requirements.txt"

echo "--------------------------------------------------------"
echo "Computer Vision Coursework - Visual Search Project"
echo "--------------------------------------------------------"

# --------------------------------------------------------
# 1. Check OS
# --------------------------------------------------------
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS system."
elif [[ "$OSTYPE" == "linux"* ]]; then
    echo "Detected Linux system."
else
    echo "⚠️  Unsupported system. This script is intended for macOS or Linux only."
    exit 1
fi

# --------------------------------------------------------
# 2. Verify Python installation
# --------------------------------------------------------
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.9+."
    exit 1
fi

# --------------------------------------------------------
# 3. Create virtual environment 
# --------------------------------------------------------
if [ ! -d "$ROOT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$ROOT_DIR/venv"
fi

# --------------------------------------------------------
# 4. Activate environment 
# --------------------------------------------------------
source "$ROOT_DIR/venv/bin/activate"

# --------------------------------------------------------
# 5. Upgrade pip and install dependencies
# --------------------------------------------------------
python -m pip install --upgrade pip --quiet

if [ -f "$REQ_FILE" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install --quiet -r "$REQ_FILE" || {
        echo "⚠️  Standard install failed, retrying with --break-system-packages..."
        pip install --break-system-packages -r "$REQ_FILE"
    }
else
    echo "requirements.txt not found. Installing core packages..."
    pip install --quiet numpy opencv-python matplotlib scikit-learn streamlit tqdm jupyter
fi

# --------------------------------------------------------
# 6. Verify key packages are present
# --------------------------------------------------------
echo "Checking essential packages..."
for pkg in numpy opencv-python matplotlib scikit-learn streamlit tqdm jupyter; do
    python -c "import ${pkg//-/_}" 2>/dev/null || {
        echo "Installing missing package: $pkg"
        pip install --quiet "$pkg"
    }
done

# --------------------------------------------------------
# 7. Download dataset if missing
# --------------------------------------------------------
if [ ! -d "$DATA_DIR" ]; then
    echo "Dataset not found. Downloading MSRC dataset..."
    mkdir -p "$ROOT_DIR/data"
    cd "$ROOT_DIR/data" || exit 1

    ZIP_URL="http://download.microsoft.com/download/3/3/9/339D8A24-47D7-412F-A1E8-1A415BC48A15/msrc_objcategimagedatabase_v2.zip"

    # Use wget or curl depending on what's available
    if command -v wget &> /dev/null; then
        wget -q "$ZIP_URL" -O msrc_dataset.zip
    else
        curl -s -L "$ZIP_URL" -o msrc_dataset.zip
    fi

    echo "Unzipping dataset..."
    unzip -oq msrc_dataset.zip -d "$ROOT_DIR/data/MSRC_ObjCategImageDatabase_v2"
    rm -f msrc_dataset.zip
    echo "✅ Dataset downloaded and extracted."
    cd "$ROOT_DIR" || exit 1
fi

# --------------------------------------------------------
# 8. Check descriptor file
# --------------------------------------------------------
if [ ! -f "$DESC_FILE" ]; then
    echo "⚠️ Descriptor file missing: $DESC_FILE"
    echo "Please run the PCA extraction notebook first."
    deactivate
    exit 1
fi

# --------------------------------------------------------
# 8½. Ensure Streamlit config directory exists (skip email prompt + valid TOML)
# --------------------------------------------------------
STREAMLIT_DIR="$HOME/.streamlit"
if [ ! -d "$STREAMLIT_DIR" ]; then
    mkdir -p "$STREAMLIT_DIR"
fi

# credentials.toml
cat > "$STREAMLIT_DIR/credentials.toml" <<EOF
[general]
email = ""
EOF

# config.toml  (correct structure with [server] section)
cat > "$STREAMLIT_DIR/config.toml" <<EOF
[server]
headless = true
enableCORS = false

[browser]
gatherUsageStats = false

# --------------------------------------------------------
# 9. Launch notebook or Streamlit app
# --------------------------------------------------------
case "$1" in
    notebook)
        echo "Launching Jupyter Notebook..."
        jupyter notebook "$NOTEBOOK"
        ;;
    app)
        echo "Launching Streamlit App..."
        streamlit run "$APP_FILE" &
        sleep 5
        python3 -m webbrowser "http://localhost:8501" || true
        wait
        ;;
    *)
        echo "Usage: bash run_project.sh [notebook | app]"
        ;;
esac
