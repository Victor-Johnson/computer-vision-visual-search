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
button:focus-visible {outline:3px solid #ff939b !important;outline-offset:3px;}
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


PRESETS = {
    'Full colour detail': SearchConfig(),
    'Simplified colour pattern': SearchConfig(pca=True, metric='L2'),
}


def choose(name):
    st.session_state.update(query_name=name, query_kind='dataset', picker_open=False, result_count=10)


def accept_upload():
    upload = st.session_state.get('photo_upload')
    if upload is None:
        return
    try:
        image = read_rgb(upload.getvalue())
    except ValueError as exc:
        st.session_state.upload_error = str(exc)
        return
    st.session_state.update(upload_image=image, query_kind='upload', picker_open=False,
                            result_count=10, upload_error=None)


def surprise():
    names = [name for name in by_name if name != st.session_state.get('query_name')]
    choose(random.choice(names))


def apply_preset(prefix):
    name = st.session_state[f'{prefix}_preset']
    if name in PRESETS:
        config = PRESETS[name]
        st.session_state[f'{prefix}_config'] = config
        for field in ('space', 'bins', 'pca', 'metric'):
            st.session_state[f'{prefix}_{field}'] = getattr(config, field)


def custom_settings(prefix):
    values = {field: st.session_state[f'{prefix}_{field}'] for field in ('space', 'bins', 'pca', 'metric')}
    allowed = VECTOR_METRICS if values['pca'] else HISTOGRAM_METRICS
    if values['metric'] not in allowed:
        values['metric'] = 'L2' if values['pca'] else 'Bhattacharyya'
        st.session_state[f'{prefix}_metric'] = values['metric']
    st.session_state[f'{prefix}_config'] = SearchConfig(**values)
    st.session_state[f'{prefix}_preset'] = 'Custom settings'


def method_controls(prefix, default='Full colour detail', guided=True):
    if f'{prefix}_config' not in st.session_state:
        st.session_state[f'{prefix}_preset'] = default
        apply_preset(prefix)
    config = st.session_state[f'{prefix}_config']
    # Restore widget state from the durable configuration after a view is hidden.
    for field in ('space', 'bins', 'pca', 'metric'):
        st.session_state.setdefault(f'{prefix}_{field}', getattr(config, field))
    st.session_state.setdefault(f'{prefix}_preset', next((n for n, c in PRESETS.items() if c == config), 'Custom settings'))
    if guided:
        st.selectbox('Search approach', tuple(PRESETS) + ('Custom settings',), key=f'{prefix}_preset',
                     on_change=apply_preset, args=(prefix,))
        st.caption('Uses the full colour pattern.' if st.session_state[f'{prefix}_preset'] == 'Full colour detail'
                   else 'Uses a compressed colour pattern.' if st.session_state[f'{prefix}_preset'] == 'Simplified colour pattern'
                   else 'Using your own combination of settings.')
    with st.expander('Advanced settings'):
        a, b = st.columns(2)
        a.selectbox('Colour space', ('HSV', 'RGB'), key=f'{prefix}_space', on_change=custom_settings, args=(prefix,))
        b.selectbox('Bins per channel', (8, 4), key=f'{prefix}_bins', on_change=custom_settings, args=(prefix,))
        st.toggle('Compress with PCA · 95% variance', key=f'{prefix}_pca', on_change=custom_settings, args=(prefix,))
        metrics = VECTOR_METRICS if st.session_state[f'{prefix}_pca'] else HISTOGRAM_METRICS
        st.selectbox('Distance metric', metrics, key=f'{prefix}_metric', on_change=custom_settings, args=(prefix,))
    return st.session_state[f'{prefix}_config']


def retrieve(config, query, exclude, limit):
    with st.spinner('Finding photos with similar colours…'):
        index = index_for(path_strings, signature, config)
        query_feature = histogram(query, config.space, config.bins)
        start = time.perf_counter()
        results = index.rank(query_feature, limit, exclude)
        duration = (time.perf_counter() - start) * 1000
    return results, duration, index.features.shape[1]


def result_grid(results, prefix, columns=4, overlap=frozenset(), technical=False):
    if not results:
        st.info('No matches are available right now. Please try another photo.')
        return
    for offset in range(0, len(results), columns):
        cells = st.columns(columns)
        for position, (name, distance) in enumerate(results[offset:offset + columns], offset + 1):
            with cells[(position - 1) % columns], st.container(border=True):
                path = by_name[name]
                st.image(thumbnail(str(path), path.stat().st_mtime_ns), width='stretch')
                st.markdown(f'**Match {position}**')
                if name in overlap:
                    st.caption('Found by both searches')
                if technical:
                    st.caption(f'{name} · Distance {distance:.4f}')
                st.button('Find photos like this', key=f'{prefix}_{name}',
                          on_click=choose, args=(name,), width='stretch')


def more_results():
    st.session_state.result_count = min(20, st.session_state.result_count + 5)


def footer():
    st.markdown('<div class="footer">VICTOR JOHNSON &nbsp; / &nbsp; Computer vision, made explorable.</div>', unsafe_allow_html=True)


st.markdown('<div class="brand">◈ &nbsp; VISUAL SEARCH</div>', unsafe_allow_html=True)
st.divider()
st.markdown('<div class="eyebrow">LOOK CLOSER. FIND CONNECTIONS.</div>', unsafe_allow_html=True)
st.title('Find photos with similar colours.')
st.markdown('<p class="intro">Choose a photo or upload your own to discover images with a similar mix of colours.</p>', unsafe_allow_html=True)

with st.spinner('Opening the photo collection…'):
    paths, skipped, signature = catalog(str(IMAGES))
if len(paths) < 2:
    st.info('The photo collection is temporarily unavailable. Please come back shortly.')
    footer()
    st.stop()
if skipped:
    st.warning('Some photos are temporarily unavailable. You can still explore the rest of the collection.')
by_name = {p.name: p for p in paths}
path_strings = tuple(map(str, paths))
st.session_state.setdefault('query_kind', None)
st.session_state.setdefault('picker_open', True)
st.session_state.setdefault('result_count', 10)
if st.session_state.query_kind == 'dataset' and st.session_state.get('query_name') not in by_name:
    st.session_state.update(query_kind=None, picker_open=True)
st.caption(f'{len(paths)} photos to explore')

if st.session_state.picker_open:
    st.subheader('Choose your starting photo')
    st.button('Surprise me', on_click=surprise)
    with st.container(key='examples'):
        example_columns = st.columns(min(6, len(paths)))
    for number, (col, i) in enumerate(zip(example_columns, np.linspace(0, len(paths) - 1, min(6, len(paths)), dtype=int)), 1):
        path = paths[i]
        with col:
            st.image(thumbnail(str(path), path.stat().st_mtime_ns), width='stretch')
            st.button(f'Try photo {number}', key=f'example_{path.name}', on_click=choose,
                      args=(path.name,), width='stretch')
    with st.expander('Upload a photo'):
        upload = st.file_uploader('Choose a photo from your device', type=['jpg', 'jpeg', 'png', 'bmp'],
                                  key='photo_upload', help='Up to 10 MB and 20 million pixels. Kept only in this session.')
        st.button('Find similar photos', type='primary', disabled=upload is None, on_click=accept_upload)
        if st.session_state.get('upload_error'):
            st.error(st.session_state.upload_error)
    if st.session_state.query_kind:
        st.button('Keep current photo', on_click=lambda: st.session_state.update(picker_open=False))

if not st.session_state.query_kind:
    footer()
    st.stop()
is_upload = st.session_state.query_kind == 'upload'
try:
    query = st.session_state.upload_image if is_upload else read_rgb(by_name[st.session_state.query_name])
except (ValueError, OSError):
    st.warning('This photo is no longer available. Please choose another one.')
    st.button('Choose another photo', on_click=lambda: st.session_state.update(picker_open=True, query_kind=None))
    st.stop()
exclude = None if is_upload else st.session_state.query_name
query_col, context_col = st.columns([1, 3], gap='large')
with query_col:
    st.image(ImageOps.pad(Image.fromarray(query), (480, 320), color='#18181c'), caption='Your photo', width='stretch')
with context_col:
    st.subheader('Where will this photo take you?')
    st.write('Explore the matches, or compare two ways of finding similar colours.')
    st.button('Change photo', on_click=lambda: st.session_state.update(picker_open=True, upload_error=None))

technical = st.toggle('Show technical details', key='technical_details')
limit = st.session_state.result_count
explore, compare, explain = st.tabs(['Similar photos', 'Compare searches', 'How it works'])
with explore:
    st.subheader('Photos with similar colours')
    st.write('Matches are based on colour, so they may show different objects.')
    config = method_controls('explore', guided=False)
    try:
        results, duration, dimensions = retrieve(config, query, exclude, limit)
        if technical:
            st.caption(f'{config.space} · {config.bins} bins/channel · {config.metric} · {dimensions} features · ranking {duration:.2f} ms (excludes feature extraction)')
        result_grid(results, 'explore', technical=technical)
    except (ValueError, OSError):
        st.error('We could not complete this search. Try another photo or different settings.')
with compare:
    st.subheader('Compare two ways to search')
    st.write('One search uses the full colour pattern. The other uses a compressed version. Compare how the results change.')
    summary = st.empty()
    first, second = st.columns(2, gap='large')
    with first:
        st.markdown('### Search 1')
        config_a = method_controls('compare_a')
    with second:
        st.markdown('### Search 2')
        config_b = method_controls('compare_b', 'Simplified colour pattern')
    try:
        results_a, time_a, dims_a = retrieve(config_a, query, exclude, limit)
        results_b, time_b, dims_b = retrieve(config_b, query, exclude, limit)
        shared = {n for n, _ in results_a} & {n for n, _ in results_b}
        summary.info(f'{len(shared)} photos found by both searches.')
        for panel, results, prefix, cfg, duration, dims in [(first, results_a, 'a', config_a, time_a, dims_a), (second, results_b, 'b', config_b, time_b, dims_b)]:
            with panel:
                if technical:
                    st.caption(f'{cfg.metric} · {dims} features · ranking {duration:.2f} ms. Lower distance means closer within this search only.')
                result_grid(results, prefix, 2, shared, technical)
    except (ValueError, OSError):
        st.error('We could not compare these searches. Try another photo or reset the search approaches.')
with explain:
    st.subheader('How we find similar photos')
    a, b, c = st.columns(3)
    a.markdown('**1. Look at the colours**\n\nWe count how much of each colour appears in your photo.')
    b.markdown('**2. Compare colour patterns**\n\nWe compare that mix with the other photos. A simplified search uses a compressed version of the pattern.')
    c.markdown('**3. Show the closest matches**\n\nPhotos with the closest colour patterns appear first. Choose a result to explore again.')
    st.markdown('#### The colours in your photo')
    st.write('Taller peaks mean more pixels have that amount of red, green, or blue. Hover over the chart to explore.')
    figure = go.Figure()
    for channel, name, colour in [(0, 'Red', '#f38b82'), (1, 'Green', '#7ed8b4'), (2, 'Blue', '#8cb8f4')]:
        counts, edges = np.histogram(query[:, :, channel], bins=32, range=(0, 256))
        figure.add_trace(go.Scatter(x=(edges[:-1] + edges[1:]) / 2, y=counts / counts.sum(), name=name,
                                   line={'color': colour, 'width': 2}, fill='tozeroy'))
    figure.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                         xaxis_title='Amount of colour · low to high', yaxis_title='Share of the photo',
                         template='plotly_dark', font=dict(color='#e8e8ed'),
                         xaxis=dict(gridcolor='#303036'), yaxis=dict(gridcolor='#303036', tickformat='.0%'),
                         paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                         legend=dict(orientation='h', y=1.15), hovermode='x unified')
    st.plotly_chart(figure, width='stretch')
    st.write('Similar colours do not always mean similar subjects. A green car can match a grassy field. The search does not recognise objects or where they appear in a photo.')
    with st.expander('Technical background'):
        st.write('Retrieval uses normalized joint RGB or HSV histograms. The chart above shows separate RGB channel distributions. Optional PCA retains 95% of dataset variance. PCA features can be negative, so Chi-Square and Bhattacharyya distances are restricted to original histograms. Distance values are not confidence percentages or comparable across metrics.')
        st.write('The CPU-only pipeline uses OpenCV, NumPy, and scikit-learn. Dataset searches exclude the query image itself. Ranking times exclude feature extraction. Original notebook evaluations remain historical coursework, not new benchmark results.')
    st.caption('Built by Victor Johnson from EEE3032 coursework at the University of Surrey. Dataset photographs: Microsoft Research, MSRC-v2.')
    st.link_button('Explore the code ↗', 'https://github.com/Victor-Johnson/computer-vision-visual-search')
if limit < min(20, len(paths) - (0 if is_upload else 1)):
    st.button('Show more', on_click=more_results)
footer()
