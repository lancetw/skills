---
name: know-your-unknowns
description: Surface unknowns — the gap between the plan in your head and the territory of real code — as interactive, self-contained HTML artifacts the user reacts to instead of describing from scratch. Use when a feature request is ambiguous, the work touches unfamiliar code, the user lacks the domain vocabulary to ask precisely, a visual direction or UI behavior is still open, a known problem has no chosen intervention, external reference code is about to be ported, an implementation plan needs a review pass, mid-implementation reality deviates from the plan, finished work needs stakeholder buy-in, or a large change is about to merge.
license: MIT
---

# Know Your Unknowns

The map is not the territory. The map is the prompt, the plan, the mental model; the territory is the real code and the real requirement. The gap between them is your **unknowns** — cheapest to find before implementation, priciest after merge.

This skill closes the gap with one move: build a **self-contained HTML artifact** that makes the unknowns concrete — blindspot cards, clickable mocks, side-by-side directions, quizzes — so the user *reacts* (click, check, pick) instead of having to *describe*. Reacting to something concrete surfaces unknowns that abstract discussion never reaches.

Techniques adapted from Thariq (@trq212), "Know Your Unknowns": <https://thariqs.github.io/html-effectiveness/unknowns/>

## Pick one technique

Diagnose the user's moment, pick ONE row, then read its reference file before generating anything. One artifact per run; if two rows genuinely fit, name both and ask.

| # | 技巧 | 階段 | Use when | Reference |
|---|------|------|----------|-----------|
| 01 | Blindspot pass 盲點掃描 | 實作前 | about to implement in an unfamiliar area of the codebase | [references/01-blindspot-pass.md](references/01-blindspot-pass.md) |
| 02 | Teach me my unknowns 先補課 | 實作前 | user's request is vague because they lack the domain vocabulary | [references/02-teach-me-my-unknowns.md](references/02-teach-me-my-unknowns.md) |
| 03 | Four design directions 四個設計方向 | 實作前 | visual / layout direction for a screen is undecided | [references/03-design-directions.md](references/03-design-directions.md) |
| 04 | Mock before you wire 先假接再實接 | 實作前 | UI behavior or placement is undecided; wiring real code would be premature | [references/04-mock-before-you-wire.md](references/04-mock-before-you-wire.md) |
| 05 | Brainstorm the intervention 介入點腦力激盪 | 實作前 | problem is known (metric, complaint) but no fix is chosen | [references/05-brainstorm-the-intervention.md](references/05-brainstorm-the-intervention.md) |
| 06 | The interview 規格訪談 | 實作前 | feature request is ambiguous and answers would change the architecture | [references/06-the-interview.md](references/06-the-interview.md) |
| 07 | Point at a reference 語意對照表 | 實作前 | about to port or imitate external reference code | [references/07-point-at-a-reference.md](references/07-point-at-a-reference.md) |
| 08 | The tweakable plan 可調整計畫 | 實作前 | a plan exists and the user should review the decisions most likely to change | [references/08-tweakable-plan.md](references/08-tweakable-plan.md) |
| 09 | Implementation notes 實作札記 | 實作中 | executing an approved plan; log every deviation as it happens | [references/09-implementation-notes.md](references/09-implementation-notes.md) |
| 10 | The buy-in doc 說服文件 | 實作後 | work is done and needs stakeholder sign-off to ship | [references/10-buy-in-doc.md](references/10-buy-in-doc.md) |
| 11 | Quiz me before I merge 合併前測驗 | 實作後 | a large or mostly-AI-written change is about to merge | [references/11-merge-quiz.md](references/11-merge-quiz.md) |

## Artifact rules (every technique)

- **Self-contained** — one `.html` file, inline CSS/JS, zero external requests (no CDN, no frameworks, no web fonts). Must work opened directly from `file://`, offline.
- **Grounded** — every card, finding, question, and table row names a real file, symbol, commit, or measurement from THIS codebase; do the legwork (read code, grep, `git log`) before writing the artifact. A claim you cannot ground gets deleted, not hedged. Invented data is allowed only inside mocks and demos, and must be obviously fake.
- **Reply assembly** — the defining interaction: chips / checkboxes / option buttons accumulate into a visible reply box with a 「複製回覆」 button (`navigator.clipboard.writeText`), so the user's clicks become their next prompt verbatim. Any artifact that asks the user something must assemble the reply for them.
- **Copyable prompts** — every suggested prompt or template in the artifact carries its own 「複製」 button.
- **Language** — artifact prose in Taiwan Traditional Chinese with Taiwan terms (程式碼 not 代碼、資料 not 數據、元件 not 組件); identifiers, paths, and code stay verbatim. If the conversation isn't in Chinese, follow the conversation's language.
- **Filename** — `unknowns-<NN>-<slug>.html` in the project root. It is a throwaway working page; tell the user they can delete it after replying.

## Workflow

1. **Diagnose** the moment → pick the technique from the table. Done when: exactly one row chosen, or a clarifying question naming the two candidate rows is sent.
2. **Read** the technique's reference file. Done when: read in this run, not recalled from memory.
3. **Legwork** — gather the real material the reference file demands (scan the code area, read the reference repo, walk `git log`, restate the plan). Done when: every section the artifact will render has real content to hold.
4. **Build & deliver** — write the artifact, report its absolute `file://` path plus one line on how to use it. Done when: the file exists and the path is in the reply.
5. **Act on the reply** — the assembled reply the user pastes back is the refined prompt; continue the work from it directly.
