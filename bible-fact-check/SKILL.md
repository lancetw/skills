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
   → use WebFetch to retrieve the page content, then review it
4. **Pasted text** — user pastes content directly in the conversation
   → review the pasted text
5. **No argument** — defaults to `bible-buddy/references/fun-facts.md`

## How to Run

1. Determine the input source
2. Read / receive the content
3. Run all 10 checks sequentially (skip checks that don't apply)
4. For each check, report findings with line numbers, or "✅ 通過" if clean
5. End with a summary table

## The 10 Checks

### 1. 重複檢查 (Duplicates)

Find entries that cover the same verse, topic, or argument.
Two entries using the same framework applied to different topics are NOT duplicates.
Two entries making the same point about the same verse ARE duplicates.

### 2. 稻草人檢查 (Strawman Arguments)

Find entries where "不是 X" and X is something nobody in Taiwan would actually
believe or confuse. The denial is only valuable when readers genuinely hold
misconception X. Test: would a Taiwan churchgoer actually think X?

### 3. 年代錯置檢查 (Anachronism)

Find entries that use post-200 CE sources (Mishnah, Talmud, Targums) to
definitively explain pre-100 CE texts (NT) with language like "這才是...的背景"
or "原始語境". Later sources CAN illustrate earlier concepts, but the language
must be hedged ("可能的背景" not "這才是"). Flag definitive claims only.

### 4. 事實錯誤檢查 (Factual Errors)

Verify:
- Historical dates
- Person attributions (who did what in which Bible chapter)
- Word meanings (Hebrew/Greek definitions)
- Scholarly claims (hapax legomenon, manuscript evidence, etc.)

### 5. 經節編號檢查 (Verse Reference Errors)

Verify every chapter:verse reference matches the actual Bible content cited.

### 6. 數量計算檢查 (Counting Errors)

Verify all numerical claims: word/character counts, verse counts, people counts,
ratios, dates.

### 7. 意味不明檢查 (Unclear Meaning)

Find entries that just state a fact or quote a verse without explaining:
- What misconception it corrects, OR
- What surprising insight it reveals, OR
- Why a Taiwan reader should care

Every entry needs a clear "so what?"

### 8. 過度簡化檢查 (Oversimplification)

Find entries that present one scholarly position as definitive when significant
debate exists. Look for:
- Minority academic views stated as fact
- Complex debates reduced to one-sided conclusions
- Words like "其實是" or "就是" on debated topics

### 9. 字數控制檢查 (Verbosity)

Compare each entry's character count to the median of the content. Flag entries
significantly longer than the median (roughly 2x or more).

### 10. 趣味門檻檢查 (Interest Threshold)

Flag entries that are too academic, too niche, or lack relevance for Taiwan
readers. Test questions:
- Would a Taiwan Sunday school teacher find this interesting?
- Does it require specialized knowledge to appreciate?
- Is it relevant to what Taiwan churches actually teach or encounter?

## Output Format

Start with the source being reviewed:

```
# 審查：[filename or "使用者提供的內容"]
```

For each check:

```
### N. 檢查名稱

[findings with line numbers, or ✅ 通過]
```

End with:

```
## 總結

| 檢查 | 結果 |
|------|------|
| 1. 重複 | X 組 |
| 2. 稻草人 | X 條 |
| ... | ... |

**共 X 個問題，跨 Y 項檢查。**
```

## Important Notes

- Use 上主 (not 耶和華 or YHWH) when referring to the divine name in reports
- Do NOT auto-fix anything. Report only.
- Be specific: include line numbers and quote the problematic text
- When in doubt, flag it — the user will decide whether to act
- Some checks may not apply to all content types (e.g., key-terms lists won't have
  strawman arguments). Skip with "N/A — 此檢查不適用於本內容"
