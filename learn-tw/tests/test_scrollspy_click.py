"""Browser test for the TOC scroll-spy: clicking a link must highlight THAT section.

The bug this guards against: the scroll-spy decided the "active" section from a
synthetic, evenly-distributed trigger model instead of the headings' real
positions. Clicking a TOC link smooth-scrolls the heading to its real spot, then
the click-lock released into that model and re-highlighted a *different* (later)
section for any heading sitting below its even-share slot — so the highlight
"跑錯位置" right after the scroll settled.

This is layout-dependent (it only shows up once headings have real, uneven
positions), so it can only be reproduced in a real browser, not by asserting on
the HTML string. The test is skipped where Playwright / its Chromium is absent.
"""

import pytest

pytest.importorskip("playwright")
from md_to_html import convert  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

# A deliberately UNEVEN document: a huge section pushes every later heading far
# below its even-share slot, which is exactly the layout the synthetic trigger
# model mis-resolves. The long tail guarantees every heading can still scroll up
# to the spy activation line, so a correct spy can highlight each one on click.
_LONG = "\n\n".join(f"填充段落第 {i} 句，用來把這個區段撐得很長很長。" * 4 for i in range(60))
_SHORT = "簡短的一段內容。"

_UNEVEN_MD = "\n\n".join(
    [
        "# 捲動定位測試",
        f"## 區段一\n\n{_SHORT}",
        f"## 區段二\n\n{_LONG}",  # huge — sinks the headings below it
        f"## 區段三\n\n{_SHORT}",
        f"## 區段四\n\n{_SHORT}",
        f"## 區段五\n\n{_SHORT}",
        f"## 區段六\n\n{_LONG}",  # long tail so every earlier heading reaches the line
    ]
)


def _clicked_vs_highlighted(tmp_path):
    """Click every TOC link; return the (clicked_href, highlighted_href) pairs."""
    html = convert(_UNEVEN_MD, timestamp="t")
    doc = tmp_path / "doc.html"
    doc.write_text(html, encoding="utf-8")

    pairs = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:  # browser binary not installed in this env
            pytest.skip(f"chromium unavailable (run `playwright install chromium`): {exc}")
        page = browser.new_page(viewport={"width": 1000, "height": 600})
        page.goto(doc.as_uri())
        n = len(page.query_selector_all('nav.toc a[href^="#"]'))
        for i in range(n):
            link = page.query_selector_all('nav.toc a[href^="#"]')[i]
            href = link.get_attribute("href")
            link.click()
            # Wait past the smooth scroll AND the 1000ms click-lock release: the
            # bug only surfaces once the lock frees update() to overrule the
            # highlight, so a shorter wait would hide it.
            page.wait_for_timeout(1600)
            active = page.query_selector("nav.toc a.active")
            pairs.append((href, active.get_attribute("href") if active else None))
        browser.close()
    return pairs


def test_toc_click_highlights_the_clicked_section(tmp_path):
    pairs = _clicked_vs_highlighted(tmp_path)
    assert len(pairs) == 6, f"expected 6 TOC links, got {len(pairs)}"
    mismatches = [(c, h) for c, h in pairs if c != h]
    assert not mismatches, (
        "clicking a TOC link must highlight that same section, but after the "
        f"scroll settled these clicks highlighted a different section "
        f"(clicked -> highlighted): {mismatches}"
    )


def _active_sequence_after_click(tmp_path):
    """Click a far section and record EVERY highlight change until it settles.

    Returns (target_href, sequence). The sequence captures transient states the
    final-state assertion above cannot see — a flash through a wrong section then
    a snap back shows up here as [target, wrong, ..., target].
    """
    html = convert(_UNEVEN_MD, timestamp="t")
    doc = tmp_path / "doc.html"
    doc.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:  # browser binary not installed in this env
            pytest.skip(f"chromium unavailable (run `playwright install chromium`): {exc}")
        page = browser.new_page(viewport={"width": 1000, "height": 600})
        page.goto(doc.as_uri())
        page.evaluate(
            """() => {
              window.__seq = [];
              const toc = document.querySelector('nav.toc');
              const rec = () => {
                const a = document.querySelector('nav.toc a.active');
                window.__seq.push(a ? a.getAttribute('href') : null);
              };
              new MutationObserver(rec).observe(
                toc, { subtree: true, attributes: true, attributeFilter: ['class'] });
            }"""
        )
        target = page.query_selector_all('nav.toc a[href^="#"]')[2]  # 區段三, far below 區段二
        thref = target.get_attribute("href")
        page.evaluate("window.__seq = []")  # start recording at the click
        target.click()
        # A stray wheel event mid-animation (real trackpads emit inertial wheel
        # events after a click) must NOT knock the highlight off the target while
        # the smooth scroll is still travelling to it.
        page.wait_for_timeout(80)
        page.evaluate("window.dispatchEvent(new WheelEvent('wheel', { deltaY: 1 }))")
        page.wait_for_timeout(1800)
        seq = page.evaluate("window.__seq")
        browser.close()
    return thref, seq


def test_toc_click_does_not_flash_through_wrong_section(tmp_path):
    target, seq = _active_sequence_after_click(tmp_path)
    # While the smooth scroll travels to the clicked section, the highlight must
    # stay on that section the whole way — it must never flash to a section the
    # scroll is merely passing through and then snap back ('先跳到錯誤的位置，再
    # 快速跳動到正確的位置').
    wrong = [h for h in seq if h != target]
    assert seq and seq[-1] == target and not wrong, (
        f"clicking {target} must keep the highlight on it, but the active "
        f"highlight flashed through other sections on the way: {seq}"
    )
