# Visual Search

**Find photos with similar colours.**

Choose a photo and see where its colours take you. Visual Search looks through 591 photos for a similar mix of colours, whether that leads to another flower, a field, or something unexpected.

I built this from my University of Surrey computer vision coursework, turning the original experiments into an app anyone can explore.

[Try the live demo](https://visual-search.victorjohnson.dev) · [My portfolio](https://victorjohnson.dev)

![Visual Search showing a query photo and its colour matches](stock-images/visual-search-hero.png)

## Give it a try

- Pick an example, upload a photo, or hit **Surprise me**.
- Browse the matches and choose **Find photos like this** to keep exploring.
- Open **Compare searches** to see how a full colour pattern compares with a compressed one. Shared matches are labelled.
- Visit **How it works** for an interactive colour chart and a short explanation.

You start with 10 matches and can show up to 20. Advanced settings are there if you want to experiment, but you don’t need them to get started. Uploaded photos stay in your session; the app doesn’t save them to disk.

## What’s happening behind the scenes?

Each photo becomes a colour histogram: a summary of how much of each colour it contains. The app compares these summaries and ranks the closest matches. The comparison view also tries PCA, which compresses the colour information while retaining 95% of the dataset’s variance.

**Similar colours don’t always mean similar objects.** A green car might match a grassy field. That’s part of what this project explores: what a simple, explainable computer vision method can do, and where it falls short. It doesn’t recognise objects or understand a scene’s meaning.

Built with **Python, Streamlit, OpenCV, Pillow, NumPy, scikit-learn, and Plotly**. Image loading and search live in `src/search/`, separately from the interface. Features are cached so repeat searches don’t rebuild them.

## Run it locally

Use **Python 3.12**, then run from the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/utils/download_dataset.py
streamlit run src/streamlit-app.py
```

Open `http://localhost:8501`. The first preparation downloads roughly 110 MB and checks the 591 photos. Later runs reuse the collection. If the download is unavailable, use a local dataset ZIP with its `Images/` folder intact:

```bash
python src/utils/download_dataset.py --archive /path/to/msrc.zip
```

## Tests and credits

Run the automated tests with:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover search calculations, ranking, upload validation, dataset preparation, and interface state. Browser checks in `tests/browser_smoke.py` exercise the desktop and mobile experience.

Created by **Victor Johnson**, developed from **EEE3032 coursework at the University of Surrey**. Photos come from Microsoft Research’s **MSRC-v2** dataset and are not included in this repository. Please follow the provider’s terms when using them.

The original notebooks and reports remain as coursework history; their results are not presented as newly verified benchmarks.
