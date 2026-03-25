# Visual Image Search

Content-based image retrieval system built on the MSRC-v2 dataset. Search for visually similar images using color histogram descriptors and multiple distance metrics, with an interactive Streamlit interface.

Built as part of the EEE3032 Computer Vision coursework.

## Features

- **Color histogram descriptors** — RGB and HSV with configurable bin resolutions (4x4x4, 8x8x8, 16x16x16)
- **PCA dimensionality reduction** — reduces descriptor size while preserving discriminative power
- **6 distance metrics** — L1, L2, Chi-Square, Cosine, Bhattacharyya, Mahalanobis
- **Precision-Recall evaluation** — quantitative retrieval performance analysis
- **Interactive UI** — Streamlit app with random or uploaded query images and ranked results

## Quick Start

### Automated Setup (Recommended)

```bash
bash run_project.sh app        # set up environment + launch Streamlit app
bash run_project.sh notebook   # set up environment + launch Jupyter notebooks
```

The script handles virtual environment creation, dependency installation, dataset download, and app launch.

### Manual Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python src/utils/download_dataset.py
streamlit run src/streamlit-app.py
```

**Requirements:** Python 3.9+

## Project Structure

```text
├── src/
│   ├── streamlit-app.py            # Interactive search interface
│   ├── extractors/
│   │   └── color_hist.py           # Color histogram feature extraction
│   └── utils/
│       ├── io_utils.py             # Image I/O helpers
│       ├── paths.py                # Path configuration
│       └── download_dataset.py     # Dataset downloader
├── notebooks/
│   ├── image_retrival.ipynb        # Main retrieval pipeline
│   ├── feature_extraction.ipynb    # Feature extraction workflow
│   ├── eda_visualizations.ipynb    # Exploratory data analysis
│   ├── eval_notebook.ipynb         # Evaluation metrics
│   └── final_eval.ipynb            # Final evaluation results
├── data/
│   ├── MSRC_ObjCategImageDatabase_v2/  # 591 dataset images
│   └── Descriptors/                    # Pre-computed descriptors (.pkl)
├── report/                         # Analysis outputs and figures
├── demo/                           # Demo video and HTML export
├── run_project.sh                  # Automated setup script
└── requirements.txt
```

## How It Works

1. **Feature Extraction** — Each image is converted to a global color histogram in HSV space, then reduced via PCA to a compact descriptor vector.
2. **Similarity Search** — A query image's descriptor is compared against the database using a chosen distance metric.
3. **Ranking** — Database images are sorted by distance and the top-K most similar results are displayed.

## Distance Metrics

| Metric | Formula |
| --- | --- |
| L1 (Manhattan) | `Σ\|a - b\|` |
| L2 (Euclidean) | `√Σ(a - b)²` |
| Chi-Square | `0.5 × Σ(a-b)² / (a+b)` |
| Cosine | `1 - (a·b) / (\|\|a\|\| × \|\|b\|\|)` |
| Bhattacharyya | `-log(Σ√(a×b))` |
| Mahalanobis | `√((a-b)ᵀ Σ⁻¹ (a-b))` |

## Tech Stack

Python · OpenCV · NumPy · scikit-learn · Streamlit
