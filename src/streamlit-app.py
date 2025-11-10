# ============================================
# Streamlit App — Visual Search Engine (Final)
# ============================================
import streamlit as st
import numpy as np
import cv2, pickle, time, random
from pathlib import Path
from io import BytesIO
from PIL import Image

# ============ Project Paths ============
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "MSRC_ObjCategImageDatabase_v2" / "Images"
DESC_PATH = ROOT / "data" / "Descriptors" / "HSV_PCA_SAFE.pkl"

# ============ Load Safe Descriptors ============
@st.cache_resource
def load_descriptors():
    with open(DESC_PATH, "rb") as f:
        db = pickle.load(f)
    desc_db = db["descriptors"]
    pca_mean = db["mean"]
    pca_components = db["components"]
    return desc_db, pca_mean, pca_components

desc_db, pca_mean, pca_components = load_descriptors()

# ============ Helper Functions ============
def safe_imread(path):
    img = cv2.imread(str(path))
    return None if img is None else cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def pca_transform(x, mean, components):
    x_centered = x - mean
    return np.dot(x_centered, components.T)

def color_histogram(img_rgb, bins=(8,8,8), space="HSV"):
    if space.upper() == "HSV":
        img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        ranges = ((0,180),(0,256),(0,256))
    else:
        img = img_rgb
        ranges = ((0,256),)*3
    hist = cv2.calcHist([img],[0,1,2],None,bins,[r for pair in ranges for r in pair])
    hist = hist.astype(np.float32)
    hist /= hist.sum() + 1e-10
    return hist.flatten()

# Distance metrics
def l1(a,b): return np.sum(np.abs(a-b))
def l2(a,b): return np.sqrt(np.sum((a-b)**2))
def chi2(a,b,eps=1e-10): return 0.5*np.sum(((a-b)**2)/(a+b+eps))
def cosine(a,b): return 1 - np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-10)
def bhatta(a,b):
    a = a / (a.sum() + 1e-10)
    b = b / (b.sum() + 1e-10)
    val = np.sum(np.sqrt(a*b))
    val = np.clip(val, 1e-10, 1) 
    return -np.log(val)
# Mahalanobis setup
X = np.array(list(desc_db.values()))
cov = np.cov(X, rowvar=False)
inv_cov = np.linalg.inv(cov + np.eye(cov.shape[0])*1e-6)
def mahalanobis(a,b,inv_cov):
    d = a - b
    return np.sqrt(np.dot(np.dot(d.T, inv_cov), d))

metric_funcs = {
    "L1": l1,
    "L2": l2,
    "Chi-Square": chi2,
    "Cosine": cosine,
    "Bhattacharyya": bhatta,
    "Mahalanobis": lambda a,b: mahalanobis(a,b,inv_cov)
}

def rank(query_vec, desc_db, dist_fn, top_k=10):
    distances = []
    for k,v in desc_db.items():
        d = dist_fn(query_vec, v)
        if np.isnan(d) or np.isinf(d):
            continue
        distances.append((k, d))
    if len(distances) == 0:
        return []
    distances.sort(key=lambda x: x[1])
    return distances[:min(top_k, len(distances))]

# ============ Streamlit UI ============
st.set_page_config(page_title="Visual Search Engine", layout="wide")
st.title("🔍 Visual Search Engine")
st.caption("Search visually similar images using PCA-reduced colour histograms.")

# Sidebar controls
st.sidebar.header("⚙️ Settings")
metric_choice = st.sidebar.selectbox("Similarity Metric", list(metric_funcs.keys()), index=5)
top_k = st.sidebar.slider("Top-K results", 5, 20, 10)
query_source = st.sidebar.radio("Query Source", ["🎲 Random from Dataset", "📤 Upload your own"])

# ============ Query Handling ============
if query_source == "📤 Upload your own":
    uploaded = st.file_uploader("Upload an image", type=["jpg","jpeg","png","bmp"])
    if uploaded:
        file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
        img_bgr = cv2.imdecode(file_bytes, 1)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        qv = color_histogram(img_rgb)
        qv_pca = pca_transform(qv, pca_mean, pca_components)
        st.image(img_rgb, caption="📤 Query Image (Uploaded)", width=300)

elif query_source == "🎲 Random from Dataset":
    # Session state for random query persistence
    if "random_name" not in st.session_state:
        st.session_state.random_name = random.choice(list(desc_db.keys()))

    # Layout: image + refresh button
    col1, col2 = st.columns([4,1])
    with col1:
        name = st.session_state.random_name
        img_rgb = safe_imread(DATA_DIR / name)

        if img_rgb is None:
            st.warning(f"⚠️ Could not load {name}. Choosing another image...")
            st.session_state.random_name = random.choice(list(desc_db.keys()))
            st.rerun()
        else:
            st.image(img_rgb, caption=f"🎲 Random Image Query: {name}", width=300)

    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.random_name = random.choice(list(desc_db.keys()))
            st.rerun()

    with st.spinner("Extracting colour histogram..."):
        qv = color_histogram(img_rgb)
        qv_pca = pca_transform(qv, pca_mean, pca_components)
else:
    st.stop()

# ============ Retrieval ============
if 'qv_pca' in locals():
    dist_fn = metric_funcs[metric_choice]
    start=time.time()
    results = rank(qv_pca, desc_db, dist_fn, top_k)
    elapsed=time.time()-start

    st.sidebar.success(f"⏱ Retrieval completed in {elapsed:.3f} s")
    st.markdown(f"### Top-{top_k} Results using **{metric_choice}** distance")

    cols = st.columns(5)
    for i,(name,dist) in enumerate( results):
        img = safe_imread(DATA_DIR / name)
        if img is not None:
            cols[i % 5].image(img, caption=f"{i+1}. {name}\n{metric_choice}={dist:.3f}", use_container_width=True)

st.sidebar.caption("Built with 🧠 Streamlit, OpenCV, NumPy, and PCA By ME !!")
