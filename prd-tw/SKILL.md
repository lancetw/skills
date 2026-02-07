---
name: prd-tw
description: Help non-technical stakeholders write clear requirements documents. Translates business needs into structured specs with user goals, workflows, and success criteria. No technical jargon. Output in Taiwan Traditional Chinese. Use when boss/PM/stakeholder wants to define what a feature should do without specifying how.
license: Proprietary
---

# Prd TW Skill

Help non-technical stakeholders write clear, actionable requirements documents that engineers can implement.

## Language Requirements

**Output MUST be in Taiwan Traditional Chinese (繁體中文)**, using Taiwan local terminology:

| Taiwan Term (Use) | Mainland Term (Avoid) |
|-------------------|----------------------|
| 使用者 | 用戶 |
| 檔案 | 文件 |
| 資料 | 數據 |
| 欄位 | 字段 |
| 介面 | 接口/界面 |

## Quick Start

```
/prd-tw
```

Or describe what you want:
> "I need a tool that lets users upload files and get reports"

## Document Structure

The generated requirements document follows this format (all in Taiwan Chinese):

### 1. 目的
One paragraph explaining what the tool/feature does and why it exists.

### 2. 核心需求
Each requirement includes:
- **需求標題** - Short descriptive name
- **使用者目標** - What the user wants in their own words (quoted)
- **這代表什麼** - Bullet points explaining what this means in practice

### 3. 使用者工作流程
Step-by-step flows showing how users interact with the system:
```
使用者：「動作或請求」
→ 系統回應
→ 使用者下一步
→ 結果
```

### 4. 本需求文件不涵蓋的內容
Explicitly lists what this document does NOT specify:
- Implementation details
- Technology choices
- UI/UX design
- Performance requirements
- Error handling strategies

### 5. 成功標準
Checkboxes (✓) listing measurable outcomes that define "done".

## Writing Principles

### Focus on WHAT, not HOW
- ✓ 「使用者可以選擇要移除哪些欄位」
- ✗ 「用下拉選單搭配勾選框」

### Use User Voice
- ✓ 使用者目標：「我需要在分享前移除敏感資料」
- ✗ 使用者目標：系統應提供資料遮蔽功能

### Be Concrete with Examples
- ✓ 「使用者看到確認訊息：『已處理 3 個檔案，每個檔案變更 2 個欄位』」
- ✗ 「使用者收到回饋」

### Avoid Technical Jargon
- ✓ 「變更紀錄」
- ✗ 「Audit log with transaction IDs」

## Workflow

1. Ask user what they want to build (if not provided)
2. Clarify the core user goals
3. Identify 3-6 core requirements
4. Define user workflows (interactive, batch, automated if applicable)
5. List what's explicitly out of scope
6. Write success criteria as checkboxes
7. Output complete document in Taiwan Traditional Chinese

## Output Location

Save as `REQUIREMENTS.md` or `[功能名稱]_需求文件.md` in the project directory.

## Example Prompts

> "Help me write requirements for a file converter"
> "I need users to be able to export reports as PDF"
> "Write a requirements doc for batch processing feature"
> "/prd-tw"

## Example Output Structure

```markdown
# [功能名稱]：需求文件

## 1. 目的
[一段話說明這個功能做什麼、為什麼需要它]

---

## 2. 核心需求

### 需求 1：[需求名稱]
使用者必須能夠 [能力描述]。

**使用者目標：**「[用使用者的話描述他們想要什麼]」

**這代表什麼：**
- [具體說明 1]
- [具體說明 2]
- [具體說明 3]

### 需求 2：[需求名稱]
...

---

## 3. 使用者工作流程

### 工作流程 A：[流程名稱]
```
使用者：「[動作]」
→ [系統回應]
→ [下一步]
→ [結果]
```

---

## 4. 本需求文件不涵蓋的內容

本文件**不規定**：
- [不包含項目 1]
- [不包含項目 2]
- ...

---

## 5. 成功標準

✓ [可衡量的成功指標 1]
✓ [可衡量的成功指標 2]
✓ [可衡量的成功指標 3]
```

## Tips for Stakeholders

1. **Start with the problem** - What pain point are you solving?
2. **Think about users** - Who will use this? What do they need?
3. **Don't solve it yet** - Describe what you want, not how to build it
4. **Give examples** - Real scenarios help engineers understand
5. **Define done** - How will you know it's successful?
