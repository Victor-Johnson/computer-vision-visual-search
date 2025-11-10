import streamlit as st
import cv2, pickle, time, sys, random
import numpy as np
from pathlib import Path
from PIL import Image

# ---------------------------------------------------
# 🔧 Dynamic path setup
# ---------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# ---------------------------------------------------
# 🧩 Utility functions
# ---------------------------------------------------
def safe_imread(path: Path):
    """Safely read an image and return an RGB numpy array or None."""
    if not path.exists():
        st.warning(f"⚠️ Missing file: {path.name}")
        return None
    img = cv2.imread(str(path))
    if img is None or img.size == 0:
        st.warning(f"⚠️ Could not read image: {path.name}")
        return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def color_histogram(img_rgb, bins=(8, 8, 8), space="HSV"):
    """Compute a normalized colour histogram."""
    if img_rgb is None:
        return None
    if space.upper() == "HSV":
        img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        ranges = ((0, 180), (0, 256), (0, 256))
    else:
        img = img_rgb
        ranges = ((0, 256),) * 3
    hist = cv2.calcHist([img], [0, 1, 2], None, bins, [r for pair in ranges for r in pair])
    hist = hist.astype(np.float32)
    hist /= hist.sum() + 1e-10
    return hist.flatten()


# ---------------------------------------------------
# 📏 Distance metrics
# ---------------------------------------------------
def l1(a, b):  return np.sum(np.abs(a - b))
def l2(a, b):  return np.sqrt(np.sum((a - b) ** 2))
def chi2(a, b, eps=1e-10): return 0.5 * np.sum(((a - b) ** 2) / (a + b + eps))
metric_funcs = {"L1": l1, "L2": l2, "Chi-Square": chi2}


def rank(query_vec, desc_db, dist_fn, top_k=10):
    """Return top_k matches ranked by chosen distance function."""
    distances = [(k, dist_fn(query_vec, v)) for k, v in desc_db.items()]
    distances.sort(key=lambda x: x[1])
    return distances[:top_k]


# ---------------------------------------------------
# 🎨 Streamlit layout
# ---------------------------------------------------
st.set_page_config(page_title="Visual Search Demo", layout="wide")
st.title("🔍 Content-Based Image Retrieval (CBIR)")
st.markdown("Upload or choose a query image to find visually similar ones using PCA-compressed descriptors.")

# Paths
DATA_DIR = ROOT / "data" / "MSRC_ObjCategImageDatabase_v2" / "Images"
DESC_PATH = ROOT / "data" / "Descriptors" / "HSV_PCA.pkl"

# ---------------------------------------------------
# 📂 Load descriptor database and PCA model
# ---------------------------------------------------
@st.cache_resource
def load_descriptors():
    if not DESC_PATH.exists():
        st.error(f"Descriptor file not found: {DESC_PATH}")
        st.stop()
    db = pickle.load(open(DESC_PATH, "rb"))
    descs = {k: v for k, v in db["descriptors"].items() if "_GT" not in k}
    pca = db.get("pca", None)
    return descs, pca

desc_db, pca_model = load_descriptors()
st.sidebar.success(f"Loaded {len(desc_db)} descriptors")

# ---------------------------------------------------
# ⚙️ Sidebar controls
# ---------------------------------------------------
st.sidebar.header("⚙️ Settings")
metric_choice = st.sidebar.selectbox("Distance Metric", list(metric_funcs.keys()), index=2)
top_k = st.sidebar.slider("Top K results", 5, 20, 10)
query_source = st.radio("Choose Query Source", ["📤 Upload", "🎲 Random from Dataset"])

# ---------------------------------------------------
# 🖼️ Query image input
# ---------------------------------------------------
img_rgb = None
query_vec = None

# --- Upload mode ---
if query_source == "📤 Upload":
    uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "bmp"])
    if uploaded:
        file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
        img_bgr = cv2.imdecode(file_bytes, 1)
        if img_bgr is not None:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            query_vec = color_histogram(img_rgb)
            if query_vec is not None and pca_model is not None:
                query_vec = pca_model.transform([query_vec])[0]
            st.image(img_rgb, caption="Query Image", width=250)
        else:
            st.error("Could not read uploaded image.")

# --- Random dataset mode ---
elif query_source == "🎲 Random from Dataset":
    tries = 0
    while tries < 10:
        name = random.choice(list(desc_db.keys()))
        img_rgb = safe_imread(DATA_DIR / name)
        if img_rgb is not None:
            query_vec = color_histogram(img_rgb)
            if query_vec is not None and pca_model is not None:
                query_vec = pca_model.transform([query_vec])[0]
            st.image(img_rgb, caption=f"Random Query: {name}", width=250)
            break
        tries += 1
    if img_rgb is None:
        st.error("No valid images found in dataset.")
        st.stop()

# ---------------------------------------------------
# 🔍 Retrieval and display
# ---------------------------------------------------
if query_vec is not None:
    dist_fn = metric_funcs[metric_choice]
    start = time.time()
    results = rank(query_vec, desc_db, dist_fn, top_k)
    elapsed = time.time() - start
    st.sidebar.write(f"⏱ Retrieval time: {elapsed:.3f} s")

    # Optional sanity check shapes
    one_vec = next(iter(desc_db.values()))
    st.sidebar.write(f"Query shape: {query_vec.shape}, DB shape: {one_vec.shape}")

    cols = st.columns(5)
    for i, (name, dist) in enumerate(results):
        img = safe_imread(DATA_DIR / name)
        if img is None:
            continue
        cols[i % 5].image(
            img,
            caption=f"{i + 1}: {name}\n{metric_choice}={dist:.3f}",
            use_container_width=True,
        )
