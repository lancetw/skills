"""★ Insight blocks must render as styled callouts, not raw blockquotes.

bible-bread / bible-buddy / bible-fact-check mandate the blockquote form
(`> ★ Insight ─…`, every line `> `-prefixed, two trailing spaces) in their
saved markdown. The converter must recognise that form — a devotional whose
Insight survives as a plain <blockquote> with literal ─ rule lines is the bug
this test reproduces.

Run: uv run --directory bible-buddy python tests/test_md_to_html_insight.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import md_to_html


# Trailing two spaces on every line are part of the bible-* convention
# (markdown hard line breaks for VS Code preview) — kept explicit via "  \n".
BLOCKQUOTE_FORM = (
    "# 每日靈修：出埃及記 3\n"
    "\n"
    "正文段落。\n"
    "\n"
    "> ★ Insight ─────────────────────────────────────  \n"
    "> ① 出埃及是第一世紀猶太人信仰的核心故事。  \n"
    "> ② 自由，是為了去敬拜。  \n"
    "> ─────────────────────────────────────────────────  \n"
)

PLAIN_FORM = """# 文件

★ Insight ─────────────────────────────────────
重點一。
─────────────────────────────────────────────────
"""


def check(name: str, md_text: str) -> None:
    html = md_to_html.convert(md_text, title="t")
    body = html[html.index("<main") :]
    assert '<div class="insight"' in body, f"{name}: no .insight callout rendered"
    assert "─────" not in body, f"{name}: literal ─ rule lines leaked into output"
    print(f"ok: {name}")


check("blockquote form (bible-* convention)", BLOCKQUOTE_FORM)
check("plain form (regression)", PLAIN_FORM)
print("all ok")
