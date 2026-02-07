---
name: learn-tw
description: Generate a personalized learning document (FOR[yourname].md) that explains a project in plain, engaging Taiwan Traditional Chinese. Covers technical architecture, codebase structure, technologies, design decisions, and lessons learned. Use when user wants to understand a codebase deeply or create project documentation for learning purposes.
license: MIT
---

# Learn TW Skill

Create engaging, personalized learning documents that explain projects in plain language.

## Language Requirements

**Output MUST be in Taiwan Traditional Chinese (繁體中文)**, using Taiwan local terminology:

| Taiwan Term (Use) | Mainland Term (Avoid) |
|-------------------|----------------------|
| 程式碼 | 代碼 |
| 資料庫 | 數據庫 |
| 資料 | 數據 |
| 軟體 | 軟件 |
| 硬體 | 硬件 |
| 網路 | 網絡 |
| 伺服器 | 服務器 |
| 記憶體 | 內存 |
| 物件 | 對象 |
| 變數 | 變量 |
| 迴圈 | 循環 |
| 陣列 | 數組 |
| 函式 | 函數 |
| 檔案 | 文件 |
| 視窗 | 窗口 |
| 滑鼠 | 鼠標 |
| 列印 | 打印 |

## Quick Start

```
/learn-tw
```

This generates a `FOR[username].md` file in the project root.

## What Gets Generated

### FOR[yourname].md Contents

1. **專案概述 (Project Overview)** - What the project does, who it's for, the problem it solves
2. **技術架構 (Technical Architecture)** - System design, data flow, key components and how they connect
3. **程式碼結構 (Codebase Structure)** - Directory layout, important files, where to find things
4. **技術選型 (Technology Stack)** - What's used and why we chose it over alternatives
5. **設計決策 (Design Decisions)** - The "why" behind architectural choices, trade-offs considered
6. **學習心得 (Lessons Learned)** - Bugs encountered, pitfalls to avoid, best practices discovered
7. **工程師思維 (How Good Engineers Think)** - Patterns, mental models, debugging approaches used

## Writing Style Guidelines

- **Engaging, not boring** - Write like explaining to a curious friend, not a textbook
- **Use analogies** - Compare complex concepts to everyday things
- **Include anecdotes** - "We tried X, it broke because Y, so we did Z"
- **Be specific** - Real file names, real error messages, real solutions
- **Show the journey** - Include the mistakes, not just the final answer

## ASCII 流程圖規則

為避免中文字元導致版面錯位，流程圖採用 **英文標籤 + 中文圖例** 的方式：

```
+--------+     +--------+     +---------+     +--------+     +--------+
| Explore| --> |  Read  | --> | Analyze | --> |  Write | --> |  Save  |
+--------+     +--------+     +---------+     +--------+     +--------+

圖例：
- Explore = 探索程式碼結構
- Read = 閱讀核心檔案
- Analyze = 分析架構模式
- Write = 撰寫學習文件
- Save = 儲存到專案根目錄
```

**規則：**
1. 圖形內使用英文標籤（確保對齊）
2. 圖形下方附上中文圖例對照
3. 標籤簡短，詳細說明放圖例

## Workflow

1. Explore codebase structure (`ls`, file patterns)
2. Read key files (entry points, configs, core modules)
3. Identify architecture patterns and tech decisions
4. Note any documented bugs/issues in git history or comments
5. Write FOR[username].md with all sections in Taiwan Traditional Chinese
6. Save to project root

## Output Location

The generated file is saved as `FOR[username].md` in the project root directory, where `[username]` is replaced with the user's name.

## Example Prompts

> "Create a learning doc for this project"
> "Help me understand this codebase"
> "Write a FOR[myname].md explaining everything"
> "/learn-tw"

## Example Output Structure

```markdown
# FOR[username].md

## 專案概述

[用一段話說明這個專案做什麼、給誰用、解決什麼問題]

---

## 技術架構

[系統設計、資料流、關鍵元件如何串接]

想像這個系統像是...（比喻）

---

## 程式碼結構

```
project/
├── src/           # 主要程式碼
│   ├── core/      # 核心邏輯
│   └── utils/     # 工具函式
├── tests/         # 測試
└── config/        # 設定檔
```

重要檔案：
- `src/main.ts` - 進入點
- `src/core/engine.ts` - 核心引擎

---

## 技術選型

| 技術 | 用途 | 為何選它 |
|------|------|----------|
| [技術名] | [用途] | [原因] |

---

## 設計決策

### 決策 1：[標題]

**問題：** [遇到什麼問題]

**選項：**
- A：[方案 A]
- B：[方案 B]

**決定：** 選 A，因為...

---

## 學習心得

### 踩過的坑

**問題：** [錯誤訊息或現象]
**原因：** [為什麼會這樣]
**解法：** [怎麼修的]
**學到：** [以後要注意什麼]

### 最佳實踐

- [實踐 1]
- [實踐 2]

---

## 工程師思維

[這個專案展現的設計模式、除錯方法、思考方式]
```
