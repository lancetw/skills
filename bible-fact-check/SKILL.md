---
name: bible-fact-check
description: >
  Systematically review biblical content through a 10-point quality checklist.
  Works with bible-buddy reference files, any file path, URLs, or text pasted
  directly in the conversation. Use when asked to review, audit, check, or
  verify biblical content. Trigger on: "檢查冷知識", "fact check", "檢查經文",
  "review bible", "幫我檢查這段", "bible-fact-check", or any request to find
  errors, duplicates, or issues in biblical reference content.
---

# Bible Fact Check

Systematically audit biblical reference content through 10 quality checks.
Report issues with specific line numbers. Never auto-fix — only report.

## Input Sources (pick one)

1. **bible-buddy reference file** — e.g., `/review-bible-buddy fun-facts.md`
   → reads from `bible-buddy/references/`
2. **Any file path** — e.g., `/review-bible-buddy /path/to/my-notes.md`
   → reads the specified file
3. **URL** — e.g., `/review-bible-buddy https://example.com/article`
   → Do NOT use WebFetch — many news sites block it with 403.
   Run `uv run --project bible-buddy bible-buddy/scripts/fetch_url.py "<URL>"` to extract article text.
   The script auto-falls back to patchright (headless Chromium) when urllib gets 403.
4. **Pasted text** — user pastes content directly in the conversation
   → review the pasted text
5. **No argument** — use AskUserQuestion to ask the user whether they want to
   paste a URL or input text. Do NOT default to any file.

## Prerequisites

1. Verify `bible-buddy/references/` exists (sibling directory or project root).
   If not found, **stop immediately** and tell the user:
   「bible-fact-check 需要 bible-buddy skill。請先安裝：`npx skills add lancetw/skills/bible-buddy`」

2. Run dependency setup (one-time):
   ```bash
   cd bible-buddy && uv sync && uv run patchright install chromium
   ```

## How to Run

1. Determine the input source
2. **Verify bible-buddy is installed** (see Prerequisites above)
3. Read / receive the content
4. Load reference files as checking criteria (read on demand, not all at once):
   - `bible-buddy/references/anachronism-timeline.md` → for checks 3, 4
   - `bible-buddy/references/commonly-misread-passages.md` → for checks 2, 4, 7, 8
   - `bible-buddy/references/yeshua-hermeneutics.md` → for check 8
5. Run all 10 checks sequentially (skip checks that don't apply)
6. For each check, report findings with line numbers, or "✅ 通過" if clean
7. End with a summary table

## The 10 Checks

### 1. 重複檢查 (Duplicates) ⟨fun-facts only⟩

Skip this check for URLs and pasted text.

Find entries that cover the same verse, topic, or argument.
Two entries using the same framework applied to different topics are NOT duplicates.
Two entries making the same point about the same verse ARE duplicates.

### 2. 稻草人檢查 (Strawman Arguments) ⟨fun-facts only⟩

Skip this check for URLs and pasted text.

Find entries where "不是 X" and X is something nobody in Taiwan would actually
believe or confuse. Cross-reference `commonly-misread-passages.md`: if the denied
X appears in the "Common Misreading" column, the denial is grounded and valid.
If X has no basis in the reference file AND no basis in Taiwan church practice,
it is likely a strawman. Test: does the misreading exist in the reference file,
or would a Taiwan churchgoer actually think X?

### 3. 年代錯置檢查 (Anachronism)

Cross-reference `anachronism-timeline.md` for every doctrine, practice, or concept
mentioned. If a doctrine has a known origin date (e.g., altar call = 1830s,
TULIP = 1618-1619, spiritual covering = 1970s), verify the content uses the
correct date and does not project it back to the first century.

Also detect **implicit** anachronistic terminology even when no verse is cited.
Scan the content for terms that match any doctrine/practice in
`anachronism-timeline.md`. If a match is found, note the actual origin date
as **supplementary context** — not as a criticism. News articles and practical
guides are not expected to cite historical origins. The goal is to give the
reader background, not to fault the author for omitting academic footnotes.

Also flag entries that use post-200 CE sources (Mishnah, Talmud, Targums) to
definitively explain pre-100 CE texts with language like "這才是...的背景".
Later sources CAN illustrate earlier concepts, but the language must be hedged
("可能的背景" not "這才是"). Flag definitive claims only.

### 4. 事實錯誤檢查 (Factual Errors)

Verify:
- Historical dates (cross-reference `anachronism-timeline.md` for known dates)
- Person attributions (who did what in which Bible chapter)
- Word meanings: if a Hebrew/Greek term appears in `commonly-misread-passages.md`'s
  "Key Hebrew/Greek Term" column, verify the content uses it correctly
- Scholarly claims (hapax legomenon, manuscript evidence, etc.)
- If the content's interpretation of a passage contradicts the "Actual First-Century
  Jewish Context" column in `commonly-misread-passages.md`, flag it
- Theological teachings without any scripture citation: if the content makes a
  theological claim (about God, the Spirit, salvation, church practice) without
  citing scripture, flag as "ungrounded teaching" (無經文根據的教導)

### 5. 經節編號檢查 (Verse Reference Errors)

Verify every chapter:verse reference matches the actual Bible content cited.

### 6. 數量計算檢查 (Counting Errors)

Verify all numerical claims: word/character counts, verse counts, people counts,
ratios, dates.

### 7. 意味不明檢查 (Unclear Meaning) ⟨fun-facts only⟩

Skip this check for URLs and pasted text.

Find entries that just state a fact or quote a verse without explaining:
- What misconception it corrects, OR
- What surprising insight it reveals, OR
- Why a Taiwan reader should care

Every entry needs a clear "so what?"

If the entry involves a Hebrew/Greek term, check whether it provides the key term
from `commonly-misread-passages.md`. Entries that discuss original language without
naming the actual word (e.g., saying "原文意思是X" without giving the Hebrew/Greek)
are weaker than those that do.

### 8. 過度簡化檢查 (Oversimplification)

Find entries that present one scholarly position as definitive when significant
debate exists. Look for:
- Minority academic views stated as fact
- Complex debates reduced to one-sided conclusions
- Words like "其實是" or "就是" on debated topics

Cross-reference `commonly-misread-passages.md`: if the content falls into a
"Common Misreading" pattern listed there, flag it. Also check `yeshua-hermeneutics.md`:
if the content mentions Jesus' teaching methods (parables, arguments from Torah),
verify it correctly identifies the method (e.g., kal va-chomer, mashal, remez)
rather than oversimplifying as generic "metaphor" or "symbolism".

### 9. 字數控制檢查 (Verbosity) ⟨fun-facts only⟩

Skip this check for URLs and pasted text.

Compare each entry's character count to the median of the content. Flag entries
significantly longer than the median (roughly 2x or more).

### 10. 趣味門檻檢查 (Interest Threshold) ⟨fun-facts only⟩

Skip this check for URLs and pasted text.

Flag entries that are too academic, too niche, or lack relevance for Taiwan
readers. Test questions:
- Would a Taiwan Sunday school teacher find this interesting?
- Does it require specialized knowledge to appreciate?
- Is it relevant to what Taiwan churches actually teach or encounter?

Use `commonly-misread-passages.md` as a relevance guide: passages listed there
with test cases from folk-religion, marketplace-theology, or charismatic-theology
are highly relevant to Taiwan. Passages tied only to foreign contexts (e.g.,
Hindu theology, Vajrayana) are less relevant unless Taiwan has that community.

## Output Format

When reviewing a **URL or pasted text** (not a bible-buddy reference file):
1. Create output folder: `~/Desktop/bible-fact-check/`
2. Write the full report to `~/Desktop/bible-fact-check/YYYYMMDD-HHmmss-<slug>.md`
   - URL → slug from domain + path (e.g., `cdn-news-org-idol-removal`)
   - Pasted text → `pasted-text`
3. Show only the summary table in the conversation, with the file path

When reviewing a **bible-buddy reference file**: output the full report in the conversation as before.

### Report structure

```
# 審查：[filename or URL or "使用者提供的內容"]
來源：[URL if applicable]
日期：[YYYY-MM-DD HH:mm:ss]
```

For each check that has findings, use a table:

```
### N. 檢查名稱

| # | 原文摘錄 | 問題說明 |
|---|---------|---------|
| 1 | 「...」 | 簡短說明 |
| 2 | 「...」 | 簡短說明 |
```

Checks with no findings: `### N. 檢查名稱 — ✅ 通過` (one line, no table)

End with a summary that **explains** the issues, not just counts them:

```
## 總結

| 檢查 | 結果 |
|------|------|
| 1. 重複 | ✅ |
| 2. 稻草人 | 2 項 |
| ... | ... |

### 主要問題說明

1. **[問題類型]** — 2-3 句白話解釋，這些問題為什麼重要、讀者該注意什麼。
2. ...
```

## Readability Rules

Reports should be easy to read for a Taiwan churchgoer, not just scholars:
- **全中文為主** — 希臘文/希伯來文只在必要時附註，不要大段英文引用
- **短段落** — 每個發現 2-3 句話就好，不要寫論文
- **白話** — 用台灣教會能理解的語言，避免學術腔
- **補充背景 ≠ 批評** — 年代錯置檢查的語氣是「補充資訊」，不是指責作者
- Reference file 引用只需標示來源名稱和關鍵事實，不要貼原文

## Important Notes

- Use 上主 (not 耶和華 or YHWH) when referring to the divine name in reports
- Do NOT auto-fix anything. Report only.
- Be specific: include line numbers and quote the problematic text
- When a finding is based on a reference file, cite it:
  「根據 anachronism-timeline.md：altar call 起源為 1830s，非 1820s」
- When in doubt, flag it — the user will decide whether to act
- Some checks may not apply to all content types (e.g., key-terms lists won't have
  strawman arguments). Skip with "N/A — 此檢查不適用於本內容"
- Reference files are at `bible-buddy/references/` relative to the skill's sibling
  directory. If running from a different location, look for them relative to the
  project root containing `bible-buddy/`
