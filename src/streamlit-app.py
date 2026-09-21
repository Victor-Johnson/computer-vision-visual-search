"""Visual Search / a colour-based image exploration studio."""
import random
import time
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
from PIL import Image, ImageOps
import streamlit as st
from search.images import discover, read_rgb
from search.engine import (SearchConfig, SearchIndex, histogram, fingerprint,
                           feature_matrix, VECTOR_METRICS, HISTOGRAM_METRICS)
from utils.paths import IMAGES, CACHE

st.set_page_config(page_title='Visual Search · Victor Johnson', page_icon='◈', layout='wide')
st.markdown('''<style>
.block-container {max-width:1320px;padding-top:2.4rem;padding-bottom:2rem;}
h1 {font-size:3.8rem !important;letter-spacing:-.065em;line-height:1.05 !important;}
h2,h3 {letter-spacing:-.035em;}
[data-testid="stAppViewContainer"] {background:#0b0b0d;}
[data-testid="stMetricValue"] {font-size:1.65rem;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:16px;}
[data-testid="stImage"] img {border-radius:10px;}
.eyebrow {color:#ff6974;font-size:.75rem;letter-spacing:.18em;font-weight:700;margin-bottom:18px;}
.intro {max-width:650px;font-size:1.12rem;color:#b8b8c1;line-height:1.7;margin:1rem 0 1.6rem;}
.brand {font-size:.9rem;font-weight:700;letter-spacing:.02em;}
.tag {display:inline-block;background:#35161c;color:#ff939b;border-radius:30px;padding:6px 12px;font-size:.75rem;}
.footer {color:#a3a3ae;font-size:.8rem;border-top:1px solid #303036;padding-top:22px;margin-top:40px;}
@media(max-width:640px){h1{font-size:2.65rem !important;}.block-container{padding:4rem 1rem 1.3rem;}
.st-key-examples [data-testid=stHorizontalBlock]{flex-wrap:wrap;}
.st-key-examples [data-testid=stColumn]{min-width:0 !important;flex:1 1 45% !important;}}
</style>''', unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def catalog(root):
    paths, skipped = discover(Path(root))
    return paths, skipped, fingerprint(paths)


@st.cache_data(show_spinner=False, max_entries=4)
def features(paths, signature, space, bins):
    return feature_matrix([Path(p) for p in paths], space, bins, CACHE, signature)


@st.cache_resource(show_spinner=False, max_entries=16)
def index_for(paths, signature, config):
    matrix = features(paths, signature, config.space, config.bins)
    return SearchIndex([Path(p).name for p in paths], matrix, config)


@st.cache_data(show_spinner=False, max_entries=700)
def thumbnail(path, modified):
    return np.asarray(ImageOps.fit(Image.fromarray(read_rgb(Path(path))), (480, 320)))


def choose(name):
    st.session_state.query_name = name
    st.session_state.query_kind = 'dataset'


def use_upload(upload):
    image = read_rgb(upload.getvalue())
    st.session_state.upload_image = image
    st.session_state.query_kind = 'upload'


def method_controls(prefix, comparison=False):
    a, b = st.columns(2)
    space = a.selectbox('Colour space', ('HSV', 'RGB'), key=f'{prefix}_space')
    bins = b.selectbox('Bins per channel', (8, 4), key=f'{prefix}_bins')
    pca = st.toggle('Compress with PCA · 95% variance', key=f'{prefix}_pca', value=comparison)
    metrics = VECTOR_METRICS if pca else HISTOGRAM_METRICS
    key = f'{prefix}_metric'
    if st.session_state.get(key) not in metrics:
        st.session_state[key] = 'L2' if pca else 'Bhattacharyya'
    metric = st.selectbox('Distance metric', metrics, key=key)
    return SearchConfig(space, bins, pca, metric)


def retrieve(config, query, exclude, limit):
    with st.spinner('Finding colour connections…'):
        index = index_for(path_strings, signature, config)
        query_feature = histogram(query, config.space, config.bins)
        start = time.perf_counter()
        results = index.rank(query_feature, limit, exclude)
        duration = (time.perf_counter() - start) * 1000
    return results, duration, index.features.shape[1]


def result_grid(results, prefix, columns=4, overlap=frozenset()):
    if not results:
        st.info('No matches available. Choose another image or check the dataset.')
        return
    for offset in range(0, len(results), columns):
        cells = st.columns(columns)
        for position, (name, distance) in enumerate(results[offset:offset + columns], offset + 1):
            with cells[(position - 1) % columns], st.container(border=True):
                path = by_name[name]
                st.image(thumbnail(str(path), path.stat().st_mtime_ns), width='stretch')
                st.markdown(f'**{position:02d}** · {name}')
                st.caption(f'Distance {distance:.4f}' + ('  ·  Shared match' if name in overlap else ''))
                st.button('Search from this image', key=f'{prefix}_{name}',
                          on_click=choose, args=(name,), width='stretch')


left, right = st.columns([5, 2])
left.markdown('<div class="brand">◈ &nbsp; VISUAL SEARCH</div>', unsafe_allow_html=True)
right.markdown('<span class="tag">Computer vision / interactive study</span>', unsafe_allow_html=True)
st.divider()
st.markdown('<div class="eyebrow">LOOK CLOSER. FIND CONNECTIONS.</div>', unsafe_allow_html=True)
st.title('A different way to see similarity.')
st.markdown('<p class="intro">Start with an image. Explore a collection through colour, compare how algorithms see, and follow the unexpected connections.</p>', unsafe_allow_html=True)

with st.spinner('Opening the collection…'):
    paths, skipped, signature = catalog(str(IMAGES))
if len(paths) < 2:
    st.info('The collection is not ready yet. Prepare the dataset to start exploring.')
    st.code('python src/utils/download_dataset.py\n# Docker: docker compose --profile setup run --rm prepare')
    st.caption('Already have the dataset ZIP? Add --archive /path/to/msrc.zip to the preparation command.')
    st.stop()
if skipped:
    st.warning(f'{len(skipped)} unreadable images were skipped. Run dataset preparation to repair the collection.')
if len(paths) != 591:
    st.warning(f'This collection contains {len(paths)} readable images; the full MSRC-v2 dataset contains 591.')
by_name = {p.name: p for p in paths}
path_strings = tuple(map(str, paths))
if st.session_state.get('query_name') not in by_name:
    choose(paths[len(paths) // 3].name)

with st.expander('Choose a starting image', expanded=True):
    source = st.radio('Query source', ('Examples', 'Random image', 'Upload'), horizontal=True)
    if source == 'Examples':
        examples = np.linspace(0, len(paths) - 1, min(6, len(paths)), dtype=int)
        with st.container(key='examples'):
            example_columns = st.columns(len(examples))
        for col, i in zip(example_columns, examples):
            path = paths[i]
            with col:
                st.image(thumbnail(str(path), path.stat().st_mtime_ns), width='stretch')
                st.button('Try this image', key=f'example_{path.name}', on_click=choose,
                          args=(path.name,), width='stretch')
    elif source == 'Random image':
        st.write('Let the collection surprise you. Each image can lead somewhere new.')
        if st.button('Surprise me', type='primary'):
            candidates = [p.name for p in paths if p.name != st.session_state.query_name]
            choose(random.choice(candidates))
    else:
        upload = st.file_uploader('Your image', type=['jpg', 'jpeg', 'png', 'bmp'],
                                  help='Up to 10 MB and 20 million pixels. Stored only in this session.')
        if upload is not None:
            if st.button('Search uploaded image', type='primary'):
                try:
                    use_upload(upload)
                except ValueError as exc:
                    st.error(str(exc))

is_upload = st.session_state.query_kind == 'upload'
query = st.session_state.upload_image if is_upload else read_rgb(by_name[st.session_state.query_name])
exclude = None if is_upload else st.session_state.query_name
query_col, context_col = st.columns([1, 2.6], gap='large')
with query_col:
    st.image(ImageOps.pad(Image.fromarray(query), (480, 320), color='#18181c'), caption='Your uploaded image' if is_upload else f'Your starting point · {exclude}', width='stretch')
with context_col:
    st.subheader('Every colour tells a story.')
    st.write('These matches share colour distributions with your image. They may show different subjects — that is part of what makes this experiment interesting.')
    a, b, c = st.columns(3)
    a.metric('Images to explore', len(paths))
    b.metric('Representation', 'Colour')
    c.metric('Processing', 'CPU only')
    limit = st.slider('Number of matches', 5, 20, 10)

explore, compare, explain = st.tabs(['Explore matches', 'Compare methods', 'How it works'])
with explore:
    with st.expander('Tune the search'):
        config = method_controls('explore')
    try:
        results, duration, dimensions = retrieve(config, query, exclude, limit)
        st.subheader('Follow the visual thread')
        st.caption(f'{config.space} · {config.bins} bins/channel · {config.metric} · {dimensions} features · ranking {duration:.2f} ms (cached index; excludes feature extraction)')
        result_grid(results, 'explore')
    except (ValueError, OSError) as exc:
        st.error(f'Search unavailable: {exc}')
with compare:
    st.subheader('One image. Two perspectives.')
    st.write('Change either method and see which images stay in the picture. Distances are meaningful only within their own method; lower means closer.')
    comparison_summary = st.empty()
    first, second = st.columns(2, gap='large')
    with first:
        st.markdown('#### Method A')
        config_a = method_controls('compare_a')
    with second:
        st.markdown('#### Method B')
        config_b = method_controls('compare_b', comparison=True)
    try:
        results_a, time_a, dims_a = retrieve(config_a, query, exclude, limit)
        results_b, time_b, dims_b = retrieve(config_b, query, exclude, limit)
        shared = {n for n, _ in results_a} & {n for n, _ in results_b}
        comparison_summary.info(f'{len(shared)} shared matches in the two result sets. Shared images are labelled below.')
        with first:
            st.caption(f'{config_a.metric} · {dims_a} features · ranking {time_a:.2f} ms')
            result_grid(results_a, 'a', 2, shared)
        with second:
            st.caption(f'{config_b.metric} · {dims_b} features · ranking {time_b:.2f} ms')
            result_grid(results_b, 'b', 2, shared)
    except (ValueError, OSError) as exc:
        st.error(f'Comparison unavailable: {exc}')
with explain:
    st.subheader('From pixels to neighbours')
    a, b, c = st.columns(3)
    a.markdown('**01 / Describe**\n\nCount how often colours appear in RGB or HSV. Each image becomes a normalized histogram, independent of its size.')
    b.markdown('**02 / Compress**\n\nOptional PCA learns shared variation across the collection and keeps 95% of its variance. It reduces dimensions, not necessarily improves matches.')
    c.markdown('**03 / Compare**\n\nCompute distances, sort the collection, and inspect the closest neighbours. The query image itself is excluded from dataset searches.')
    st.markdown('#### The colour signature of your query')
    figure = go.Figure()
    for channel, name, colour in [(0, 'Red', '#f38b82'), (1, 'Green', '#7ed8b4'), (2, 'Blue', '#8cb8f4')]:
        counts, edges = np.histogram(query[:, :, channel], bins=32, range=(0, 256))
        figure.add_trace(go.Scatter(x=(edges[:-1] + edges[1:]) / 2, y=counts / counts.sum(),
                                   name=name, line={'color': colour, 'width': 2}, fill='tozeroy'))
    figure.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                         xaxis_title='Channel intensity', yaxis_title='Proportion of pixels',
                         template='plotly_dark', font=dict(color='#e8e8ed'),
                         xaxis=dict(gridcolor='#303036'), yaxis=dict(gridcolor='#303036'),
                         paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                         legend=dict(orientation='h', y=1.15), hovermode='x unified')
    st.plotly_chart(figure, width='stretch')
    st.caption('This chart shows separate RGB channel distributions for interpretation. Retrieval uses a joint three-dimensional RGB or HSV histogram.')
    st.markdown('#### What this system can — and cannot — see')
    st.write('Global histograms capture colour, but discard where objects are and what they mean. A green car can resemble a field; two similar objects under different lighting can appear far apart. PCA features can be negative, so Chi-Square and Bhattacharyya are available only for the original histograms.')
    st.write('Built by Victor Johnson from EEE3032 Computer Vision coursework at the University of Surrey. The MSRC-v2 collection is credited to Microsoft Research. Original experiments remain in the repository as historical coursework; this demo does not claim new benchmark accuracy.')
    st.link_button('Explore the code ↗', 'https://github.com/Victor-Johnson/computer-vision-visual-search')
st.markdown('<div class="footer">VICTOR JOHNSON &nbsp; / &nbsp; Computer vision, made explorable.<br>Python · OpenCV · NumPy · scikit-learn · Streamlit</div>', unsafe_allow_html=True)
