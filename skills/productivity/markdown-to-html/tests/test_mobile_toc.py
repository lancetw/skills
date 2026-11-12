"""Browser test for the mobile TOC drawer.

Two guarantees that only hold in a real, narrow viewport (string assertions on
the HTML cannot see layout):

1. The fixed control cluster must NOT sit on top of the page content. On phones
   the buttons used to overlap the H1 / 產生時間 line; the mobile top padding has
   to push the first content below the cluster's bottom edge.
2. The sidebar TOC is hidden on phones, so it must be reachable: tapping 目錄
   slides the drawer in from the left, and tapping a TOC entry closes it again.

Layout-dependent, so it runs in Chromium and is skipped where Playwright / its
browser binary is absent.
"""

import pytest

pytest.importorskip("playwright")
from md_to_html import convert  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

_MD = "\n\n".join(
    [
        "# 手機版測試標題",
        "## 區段一\n\n內容一。",
        "## 區段二\n\n內容二。",
        "## 區段三\n\n內容三。",
    ]
)

# A TOC with many entries — taller than a short phone screen — to test drawer scroll.
_MANY_MD = "# 長目錄測試\n\n" + "\n\n".join(f"## 區段{i}\n\n內容{i}。" for i in range(1, 22))


def test_drawer_scrolls_when_toc_overflows(tmp_path):
    # The reported bug: a TOC taller than the phone screen overflowed the drawer with
    # no vertical scrollbar, so lower entries were unreachable. The drawer must have a
    # definite (viewport) height so the long list scrolls inside it.
    html = convert(_MANY_MD, timestamp="t")
    doc = tmp_path / "doc.html"
    doc.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:  # browser binary not installed in this env
            pytest.skip(f"chromium unavailable (run `playwright install chromium`): {exc}")
        page = browser.new_page(viewport={"width": 390, "height": 480})  # short phone
        page.goto(doc.as_uri())
        page.evaluate("window.toggleToc()")
        page.wait_for_timeout(300)
        info = page.evaluate(
            """() => {
              const n = document.querySelector('nav.toc');
              n.scrollTop = 9999;                       // try to scroll to the bottom
              return {overflows: n.scrollHeight > n.clientHeight + 1, scrolledTo: n.scrollTop};
            }"""
        )
        browser.close()
    assert info["overflows"], "a tall TOC must overflow the fixed-height drawer"
    assert info["scrolledTo"] > 0, "the drawer must scroll to reach the lower TOC entries"


def _page(tmp_path, p, width=390, height=780):
    html = convert(_MD, timestamp="t")
    doc = tmp_path / "doc.html"
    doc.write_text(html, encoding="utf-8")
    try:
        browser = p.chromium.launch()
    except Exception as exc:  # browser binary not installed in this env
        pytest.skip(f"chromium unavailable (run `playwright install chromium`): {exc}")
    page = browser.new_page(viewport={"width": width, "height": height})
    page.goto(doc.as_uri())
    return browser, page


def test_menu_sits_with_the_toc_column_on_desktop(tmp_path):
    # The orphaned-menu bug: the menu was fixed to the far-left viewport edge, so on
    # a centred wide layout it floated far from the TOC. It must now sit at the top
    # of the TOC column — its left edge aligned with the TOC, not at the page edge.
    with sync_playwright() as p:
        browser, page = _page(tmp_path, p, width=1280, height=820)
        nav = page.query_selector("nav.toc").bounding_box()
        menu = page.query_selector(".toc-controls").bounding_box()
        browser.close()
    assert menu["x"] >= nav["x"] - 1, (
        f"menu (x={menu['x']:.1f}) should align with the TOC column (x={nav['x']:.1f}), "
        "not float at the far-left viewport edge"
    )


def test_opener_does_not_cover_content_on_mobile(tmp_path):
    # With a TOC, the only floating control on phones is the 目錄 opener (the menu
    # itself lives inside the drawer). It must not sit on top of the page content.
    with sync_playwright() as p:
        browser, page = _page(tmp_path, p)
        opener = page.query_selector(".toc-toggle").bounding_box()
        meta = page.query_selector(".meta").bounding_box()  # first content line
        # The first content line must start at or below the opener's bottom.
        assert meta["y"] >= opener["y"] + opener["height"], (
            f"opener overlaps content: opener bottom={opener['y'] + opener['height']:.1f}, "
            f"content top={meta['y']:.1f}"
        )
        # And it must stay PINNED on scroll (it is fixed) — a static opener would
        # scroll off the top and stop being reachable.
        page.evaluate("window.scrollTo(0, 900)")
        page.wait_for_timeout(150)
        after = page.query_selector(".toc-toggle").bounding_box()
        browser.close()
    assert abs(after["y"] - opener["y"]) < 1, (
        f"opener must stay fixed on scroll, but moved from y={opener['y']:.1f} to {after['y']:.1f}"
    )


def test_toc_button_opens_drawer_and_entry_closes_it(tmp_path):
    with sync_playwright() as p:
        browser, page = _page(tmp_path, p)
        width = page.viewport_size["width"]

        # Closed: the drawer is translated fully off the left edge.
        closed = page.query_selector("nav.toc").bounding_box()
        assert closed["x"] + closed["width"] <= 1, f"drawer should start off-screen: {closed}"

        # Tap 目錄: the drawer slides into view (left edge at/above 0, on screen).
        page.click(".toc-toggle")
        page.wait_for_timeout(350)  # past the .22s slide
        opened = page.query_selector("nav.toc").bounding_box()
        assert opened["x"] >= 0 and opened["x"] < width, f"drawer should be on-screen: {opened}"
        assert page.evaluate("document.body.classList.contains('toc-open')")

        # Tap a TOC entry: it navigates AND closes the drawer.
        page.click('nav.toc a[href^="#"]')
        page.wait_for_timeout(350)
        assert not page.evaluate("document.body.classList.contains('toc-open')")
        browser.close()
