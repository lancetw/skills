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

    if not os.path.exists(facts_path):
        print("⚠ references/fun-facts.md not found")
        sys.exit(1)

    facts = []
    with open(facts_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("- "):
                facts.append(line[2:])

    if exclude:
        facts = [f for f in facts if exclude not in f]

    if not facts:
        print("⚠ No facts available")
        sys.exit(1)

    print(random.choice(facts))


if __name__ == "__main__":
    main()
