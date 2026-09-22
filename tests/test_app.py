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


def select_example(app):
    app.button(key='example_00.png').click().run()
    assert not app.exception
    return app


def test_initial_choice_and_picker(app, monkeypatch):
    assert not app.exception
    assert app.session_state['query_kind'] is None
    assert not app.tabs
    assert not app.selectbox
    assert not app.slider
    select_example(app)
    assert app.session_state['query_name'] == '00.png'
    assert app.session_state['picker_open'] is False
    assert not any(b.key and b.key.startswith('example_') for b in app.button)
    next(b for b in app.button if b.label == 'Change photo').click().run()
    assert app.session_state['query_name'] == '00.png'
    assert app.session_state['picker_open']
    next(b for b in app.button if b.label == 'Keep current photo').click().run()
    assert not app.session_state['picker_open']


def test_more_details_and_result_search(app):
    select_example(app)
    def names():
        return [b.key for b in app.button if b.key and b.key.startswith('explore_')]
    original = names()
    assert len(original) == 10
    app.toggle(key='technical_details').set_value(True).run()
    assert names() == original
    next(b for b in app.button if b.label == 'Show more').click().run()
    assert len(names()) == 15
    next(b for b in app.button if b.label == 'Show more').click().run()
    assert len(names()) == 20
    assert not any(b.label == 'Show more' for b in app.button)
    key = names()[0]
    app.button(key=key).click().run()
    assert app.session_state['query_name'] == key.removeprefix('explore_')
    assert app.session_state['result_count'] == 10
    assert not app.exception


def test_presets_and_compatibility(app):
    select_example(app)
    assert not app.session_state['compare_a_config'].pca
    assert app.session_state['compare_a_config'].metric == 'Bhattacharyya'
    assert app.session_state['compare_b_config'].pca
    assert app.session_state['compare_b_config'].metric == 'L2'
    app.selectbox(key='compare_b_space').set_value('RGB').run()
    assert app.selectbox(key='compare_b_preset').value == 'Custom settings'
    assert app.selectbox(key='compare_a_space').value == 'HSV'
    app.selectbox(key='compare_b_preset').set_value('Full colour detail').run()
    assert app.session_state['compare_b_config'].space == 'HSV'
    assert app.session_state['compare_b_config'].metric == 'Bhattacharyya'
    app.toggle(key='compare_b_pca').set_value(True).run()
    assert app.session_state['compare_b_config'].metric == 'L2'
    assert 'Bhattacharyya' not in app.selectbox(key='compare_b_metric').options
    app.selectbox(key='compare_b_preset').set_value('Simplified colour pattern').run()
    assert app.session_state['compare_b_config'].pca
    assert app.session_state['compare_b_config'].bins == 8
    assert not app.exception


def test_surprise_preserves_settings(app):
    select_example(app)
    app.selectbox(key='explore_space').set_value('RGB').run()
    next(b for b in app.button if b.label == 'Change photo').click().run()
    next(b for b in app.button if b.label == 'Surprise me').click().run()
    assert app.session_state['query_name'] != '00.png'
    assert app.session_state['explore_config'].space == 'RGB'
    assert not app.session_state['picker_open']
    assert not app.exception


def test_uploaded_query_session(app):
    app.session_state['upload_image'] = np.full((10, 10, 3), 128, dtype=np.uint8)
    app.session_state['query_kind'] = 'upload'
    app.session_state['picker_open'] = False
    app.run()
    next(b for b in app.button if b.label == 'Show more').click().run()
    assert app.session_state['query_kind'] == 'upload'
    assert not app.exception


def test_missing_dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(utils.paths, 'IMAGES', tmp_path / 'missing')
    st.cache_resource.clear()
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert 'temporarily unavailable' in app.info[0].value
    assert not app.code
