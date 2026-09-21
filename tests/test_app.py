from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest
import streamlit as st
import utils.paths

APP = Path(__file__).resolve().parents[1] / 'src/streamlit-app.py'


@pytest.fixture
def app(tmp_path, monkeypatch):
    root = tmp_path / 'images'
    root.mkdir()
    rng = np.random.default_rng(7)
    for i in range(24):
        Image.fromarray(rng.integers(0, 256, (24, 24, 3), dtype=np.uint8)).save(root / f'{i:02}.png')
    monkeypatch.setattr(utils.paths, 'IMAGES', root)
    monkeypatch.setattr(utils.paths, 'CACHE', tmp_path / 'cache')
    st.cache_resource.clear()
    st.cache_data.clear()
    return AppTest.from_file(str(APP), default_timeout=30).run()


def test_interactions(app):
    assert not app.exception
    app.button(key='example_00.png').click().run()
    assert app.session_state['query_name'] == '00.png'
    app.slider[0].set_value(15).run()
    assert app.session_state['query_name'] == '00.png'
    app.toggle(key='explore_pca').set_value(True).run()
    assert app.selectbox(key='explore_metric').value == 'L2'
    assert 'Bhattacharyya' not in app.selectbox(key='explore_metric').options
    button = next(b for b in app.button if b.key.startswith('explore_'))
    target = button.key.removeprefix('explore_')
    button.click().run()
    assert app.session_state['query_name'] == target
    app.selectbox(key='compare_b_space').set_value('RGB').run()
    assert app.selectbox(key='compare_a_space').value == 'HSV'
    app.radio[0].set_value('Random image').run()
    next(b for b in app.button if b.label == 'Surprise me').click().run()
    assert app.session_state['query_name'] != target
    assert not app.exception


def test_uploaded_query_session(app):
    # Streamlit AppTest does not provide a file-uploader driver. Browser tests cover
    # actual upload; this checks the same session state survives control changes.
    app.session_state['upload_image'] = np.full((10, 10, 3), 128, dtype=np.uint8)
    app.session_state['query_kind'] = 'upload'
    app.run()
    app.slider[0].set_value(5).run()
    assert app.session_state['query_kind'] == 'upload'
    assert not app.exception


def test_missing_dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(utils.paths, 'IMAGES', tmp_path / 'missing')
    st.cache_resource.clear()
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert 'not ready' in app.info[0].value
