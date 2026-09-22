"""Exercise the app in a browser; set CAPTURE_SCREENSHOTS=0 for live verification."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get('VISUAL_SEARCH_URL', 'http://127.0.0.1:8501')
CAPTURE = os.environ.get('CAPTURE_SCREENSHOTS', '1') != '0'


def settled(page):
    expect(page.locator('[data-testid="stStatusWidget"]')).to_have_count(0, timeout=60000)
    page.wait_for_function('Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)')
    assert page.locator('[data-testid="stException"]').count() == 0


def ready(page, selected=False):
    expect(page.get_by_role('heading', name='Find photos with similar colours.')).to_be_visible(timeout=60000)
    expect(page.get_by_role('button', name='Find photos like this' if selected else 'Try photo 1').first).to_be_visible(timeout=60000)
    settled(page)


def screenshot(page, name, full=True):
    if not CAPTURE:
        return
    settled(page)
    original = page.viewport_size
    if full:
        height = page.locator('[data-testid="stMain"]').evaluate('(el) => el.scrollHeight')
        page.set_viewport_size({'width': original['width'], 'height': min(height + 80, 14000)})
    page.screenshot(path=str(ROOT / 'stock-images' / name), full_page=True)
    page.set_viewport_size(original)


if CAPTURE:
    (ROOT / 'stock-images').mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    page.goto(URL)
    ready(page)
    expect(page.get_by_role('tab')).to_have_count(0)
    expect(page.get_by_text('CPU only', exact=True)).to_have_count(0)
    expect(page.get_by_role('heading', name='Photos with similar colours', exact=True)).to_have_count(0)
    # Native buttons remain keyboard-operable with an explicit visible focus ring.
    page.get_by_role('button', name='Try photo 1').focus()
    assert page.get_by_role('button', name='Try photo 1').evaluate('(el) => el === document.activeElement')
    page.keyboard.press('Enter')
    ready(page, True)
    expect(page.get_by_role('button', name='Try photo 1')).to_have_count(0)
    panel = page.get_by_role('tabpanel').filter(has=page.get_by_role('heading', name='Photos with similar colours', exact=True))
    expect(panel.get_by_role('button', name='Find photos like this')).to_have_count(10)
    screenshot(page, 'visual-search-desktop.png')
    screenshot(page, 'visual-search-hero.png', full=False)
    page.get_by_role('button', name='Show more', exact=True).click()
    settled(page)
    expect(panel.get_by_role('button', name='Find photos like this')).to_have_count(15)
    page.get_by_role('button', name='Show more', exact=True).click()
    settled(page)
    expect(panel.get_by_role('button', name='Find photos like this')).to_have_count(20)
    panel.get_by_role('button', name='Find photos like this').first.click()
    ready(page, True)
    expect(panel.get_by_role('button', name='Find photos like this')).to_have_count(10)
    page.get_by_role('tab', name='Compare searches').click()
    expect(page.get_by_role('heading', name='Compare two ways to search')).to_be_visible()
    expect(page.get_by_text('photos found by both searches.', exact=False)).to_be_visible()
    screenshot(page, 'visual-search-compare.png')
    page.get_by_role('tab', name='How it works').click()
    expect(page.locator('.js-plotly-plot')).to_be_visible()
    screenshot(page, 'visual-search-how-it-works.png')
    if CAPTURE:
        page.get_by_role('tabpanel').filter(has=page.get_by_role('heading', name='How we find similar photos')).screenshot(path=str(ROOT / 'stock-images/visual-search-colour-analysis.png'))
    page.get_by_role('tab', name='Similar photos').click()
    page.get_by_role('button', name='Change photo').click()
    settled(page)
    expect(panel.get_by_role('button', name='Find photos like this')).to_have_count(10)
    page.get_by_text('Upload a photo', exact=True).click()
    image_path = next((ROOT / 'data/MSRC_ObjCategImageDatabase_v2/Images').glob('*.bmp'))
    page.locator('input[type=file]').set_input_files(str(image_path))
    expect(page.get_by_role('button', name='Find similar photos', exact=True)).to_be_enabled()
    page.wait_for_timeout(500)
    page.get_by_role('button', name='Find similar photos', exact=True).click()
    ready(page, True)
    expect(page.locator('input[type=file]')).to_have_count(0)
    page.get_by_role('button', name='Change photo').click()
    page.get_by_text('Upload a photo', exact=True).click()
    page.locator('input[type=file]').set_input_files({'name': 'broken.png', 'mimeType': 'image/png', 'buffer': b'broken'})
    expect(page.get_by_role('button', name='Find similar photos', exact=True)).to_be_enabled()
    page.wait_for_timeout(500)
    page.get_by_role('button', name='Find similar photos', exact=True).click()
    expect(page.get_by_text('This file could not be read.', exact=False)).to_be_visible(timeout=15000)
    expect(panel.get_by_role('button', name='Find photos like this')).to_have_count(10)
    settled(page)
    mobile = browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, device_scale_factor=1)
    mobile.goto(URL)
    ready(mobile)
    screenshot(mobile, 'visual-search-mobile-cover.png', full=False)
    mobile.get_by_role('button', name='Surprise me').click()
    ready(mobile, True)
    assert mobile.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    expect(mobile.get_by_role('button', name='Try photo 1')).to_have_count(0)
    screenshot(mobile, 'visual-search-mobile.png')
    mobile.get_by_role('tab', name='Compare searches').click()
    first = mobile.get_by_role('heading', name='Search 1', exact=True)
    second = mobile.get_by_role('heading', name='Search 2', exact=True)
    assert second.bounding_box()['y'] > first.bounding_box()['y']
    assert mobile.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    print('Browser smoke passed: initial choice, keyboard selection, pagination, result search, comparisons, chart, valid/corrupt uploads, mobile stacking.')
    browser.close()
