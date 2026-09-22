# Visual Search — portfolio screenshots

Real captures of the running black-and-red application, using the MSRC-v2 collection. These are project screenshots, not generic stock photography or generated mockups. Dataset photographs are credited to Microsoft Research; application design and implementation are by Victor Johnson.

| Asset | Suggested use | Suggested caption / alt text |
| --- | --- | --- |
| `visual-search-hero.png` | GitHub introduction or portfolio opening | A black-and-red image-search interface lets visitors explore a collection through colour. |
| `visual-search-desktop.png` | Full product overview | From sample query to ranked neighbours: the complete visual search experience. |
| `visual-search-compare.png` | Engineering discussion | Two guided search approaches share the same photo, with overlapping matches labelled for comparison. |
| `visual-search-how-it-works.png` | Case-study explanation | An accessible explanation connects image histograms, PCA, and distance-based retrieval. |
| `visual-search-colour-analysis.png` | Technical detail image | Interactive RGB distributions explain the query's colour signature and the limits of global histograms. |
| `visual-search-mobile.png` | Responsive design section | The same gallery and retrieval workflow adapts to a narrow mobile screen. |
| `visual-search-mobile-cover.png` | Mobile preview thumbnail | Choose a photo first using the compact two-column mobile example gallery. |

## Portfolio copy starter

**Visual Search — exploring image similarity through colour**

I turned a computer vision coursework pipeline into an interactive product that makes classical image retrieval approachable. Visitors can upload a query, explore related images, and compare how different representations and distance metrics change the results.

The interface combines a black-and-red gallery, an interactive colour-distribution chart, and clear explanations of the model's limitations. Underneath, a reproducible feature pipeline separates image decoding, histogram extraction, optional PCA, and ranking. Metric compatibility checks prevent histogram-only distances from being applied to signed PCA features.

The application runs in a non-root Docker container with persistent dataset storage, cached features, and Nginx reverse-proxy support. Automated numerical and interface tests complement real browser checks on desktop and mobile. The project demonstrates an interpretable colour-based baseline; it does not claim semantic image understanding or new benchmark accuracy.

## Refresh the assets

With the dataset prepared and the app running:

```bash
python tests/browser_smoke.py
```

Set `VISUAL_SEARCH_URL` for another running instance. The script waits for images to finish loading, captures the real UI, and exercises upload and navigation interactions. Full-page images suit detailed writeups; the hero and mobile-cover images are viewport captures. Keep captions about measured accuracy or speed separate unless supported by a dedicated evaluation.
