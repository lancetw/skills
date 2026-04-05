#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Pick a random fun fact for the "你知道嗎？" feature.

Reads references/fun-facts.md and outputs one random fact.

Usage:
    uv run scripts/random_fact.py [--exclude KEYWORD]

Examples:
    uv run scripts/random_fact.py
    uv run scripts/random_fact.py --exclude 以賽亞書
"""

import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    exclude = None
    if "--exclude" in sys.argv:
        idx = sys.argv.index("--exclude")
        if idx + 1 < len(sys.argv):
            exclude = sys.argv[idx + 1]

    facts_path = os.path.join(os.path.dirname(__file__), "..", "references", "fun-facts.md")

    # Hardcoded fallbacks in case fun-facts.md is missing or empty
    FALLBACK_FACTS = [
        "希伯來文聖經沒有標點符號——所有的章節劃分都是中世紀才加上的，有時會切斷原本連貫的思想。",
        "死海古卷中的以賽亞書卷軸（1QIsaᵃ）是目前最完整的希伯來聖經手抄本，比馬索拉文本早了約一千年。",
        "「阿們」（אָמֵן）在希伯來文中的意思是「確實如此」或「我信靠」，字根 א-מ-נ 與 emunah（信實）相同。",
    ]

    if not os.path.exists(facts_path):
        print(random.choice(FALLBACK_FACTS))
        return

    facts = []
    with open(facts_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("- "):
                facts.append(line[2:])

    if exclude:
        facts = [f for f in facts if exclude not in f]

    if not facts:
        facts = FALLBACK_FACTS

    print(random.choice(facts))


if __name__ == "__main__":
    main()
