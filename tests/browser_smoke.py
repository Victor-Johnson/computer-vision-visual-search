"""Run against a prepared app; writes real screenshots to stock-images/."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get('VISUAL_SEARCH_URL', 'http://127.0.0.1:8501')


def ready(page):
    expect(page.get_by_role('heading', name='A different way to see similarity.')).to_be_visible(timeout=60000)
    expect(page.get_by_role('button', name='Search from this image').first).to_be_visible(timeout=60000)
    expect(page.locator('[data-testid="stStatusWidget"]')).to_have_count(0, timeout=60000)
    page.wait_for_function('Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)')
    assert page.locator('[data-testid="stException"]').count() == 0


def screenshot(page, name):
    expect(page.locator('[data-testid="stStatusWidget"]')).to_have_count(0, timeout=60000)
    page.wait_for_function('Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)')
    original = page.viewport_size
    height = page.locator('[data-testid="stMain"]').evaluate('(el) => el.scrollHeight')
    page.set_viewport_size({'width': original['width'], 'height': min(height + 80, 14000)})
    page.screenshot(path=str(ROOT / 'stock-images' / name), full_page=True)
    page.set_viewport_size(original)


(ROOT / 'stock-images').mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 1500}, device_scale_factor=1)
    page.goto(URL)
    ready(page)
    screenshot(page, 'visual-search-desktop.png')
    page.screenshot(path=str(ROOT / 'stock-images/visual-search-hero.png'))
    page.get_by_role('button', name='Try this image').first.click()
    ready(page)
    page.get_by_role('button', name='Search from this image').first.click()
    ready(page)
    page.get_by_role('tab', name='Compare methods').click()
    expect(page.get_by_text('One image. Two perspectives.')).to_be_visible()
    expect(page.get_by_text('shared matches in the two result sets.', exact=False)).to_be_visible()
    screenshot(page, 'visual-search-compare.png')
    page.get_by_role('tab', name='How it works').click()
    expect(page.locator('.js-plotly-plot')).to_be_visible()
    screenshot(page, 'visual-search-how-it-works.png')
    page.get_by_role('tabpanel').filter(has=page.get_by_role('heading', name='From pixels to neighbours')).screenshot(path=str(ROOT / 'stock-images/visual-search-colour-analysis.png'))
    page.get_by_role('tab', name='Explore matches').click()
    page.get_by_text('Upload', exact=True).click()
    image_path = next((ROOT / 'data/MSRC_ObjCategImageDatabase_v2/Images').glob('*.bmp'))
    page.locator('input[type=file]').set_input_files(str(image_path))
    expect(page.get_by_role('button', name='Search uploaded image')).to_be_enabled()
    page.wait_for_timeout(1000)
    page.get_by_role('button', name='Search uploaded image').click()
    expect(page.get_by_text('Your uploaded image', exact=True)).to_be_visible()
    page.locator('input[type=file]').set_input_files({'name': 'broken.png', 'mimeType': 'image/png', 'buffer': b'broken'})
    expect(page.get_by_role('button', name='Search uploaded image')).to_be_enabled()
    page.wait_for_timeout(1000)
    page.get_by_role('button', name='Search uploaded image').click()
    expect(page.get_by_text('This file could not be read.', exact=False)).to_be_visible(timeout=15000)
    assert page.locator('[data-testid="stException"]').count() == 0
    mobile = browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, device_scale_factor=1)
    mobile.goto(URL)
    ready(mobile)
    assert mobile.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    screenshot(mobile, 'visual-search-mobile.png')
    mobile.screenshot(path=str(ROOT / 'stock-images/visual-search-mobile-cover.png'))
    print('Browser smoke passed: examples, result search, comparison, chart, valid/corrupt uploads, mobile width.')
    browser.close()
