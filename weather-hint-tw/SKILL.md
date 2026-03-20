---
name: weather-hint-tw
description: 查詢即時天氣，用友善同事的語氣提醒。自動偵測 IP 位置，顯示天氣卡片 + 貼心聊天。當使用者說「天氣」「weather」「要不要帶傘」「會下雨嗎」「外面冷嗎」「明天天氣」或任何跟出門穿搭、天氣狀況有關的話題時，都應該觸發這個 skill。即使使用者只是隨口提到天氣，也可以用。支援 WEATHER_CITY 環境變數覆蓋位置。
---

# 天氣提醒

## 查詢天氣

```bash
uv run "$(dirname -- "${BASH_SOURCE[0]:-$0}")/scripts/fetch-weather.py"
```

如果上面的相對路徑不行，用 skill 安裝路徑：

```bash
uv run <skill-directory>/scripts/fetch-weather.py
```

支援 `WEATHER_CITY` 環境變數或傳參數覆蓋位置（如 `uv run ... Tokyo`）。
純 Python（只用標準庫），零暫存檔，並行 API 呼叫，輸出一行 JSON。

## 怎麼回應

1. 跑腳本取得 JSON
2. **讀 `references/prompt-guide.md`**（語氣、時段、台灣用語）
3. 用 `card` 的值組成 code block 卡片（每個欄位一行）
4. 根據 `data` + prompt-guide 寫 3-5 句友善聊天
5. 卡片 + 聊天一起輸出

**如果腳本失敗**（網路斷、API 掛、timeout）：不要假裝有資料。直接跟使用者說「抱歉，天氣資料暫時抓不到，等一下再試試。」

## 參考文件

| 文件 | 內容 | 何時讀 |
|------|------|--------|
| `references/prompt-guide.md` | 語氣、時段關心、台灣用語、數字規則 | **每次都讀** |
| `references/data-fields.md` | JSON 欄位說明、活用時機 | 不確定欄位意思時讀 |
| `assets/examples.md` | 各情境範例（晴/雨/熱/補班） | 想看範例時讀 |
