---
name: weather-hint-tw
description: 查詢即時天氣，用友善同事的語氣提醒。自動偵測 IP 位置，顯示天氣卡片 + 貼心聊天。當使用者說「天氣」「weather」「要不要帶傘」「會下雨嗎」「外面冷嗎」「明天天氣」或任何跟出門穿搭、天氣狀況有關的話題時，都應該觸發這個 skill。即使使用者只是隨口提到天氣，也可以用。支援 WEATHER_CITY 環境變數覆蓋位置。
---

# 天氣提醒

## 查詢天氣

```bash
uv run "$(dirname -- "${BASH_SOURCE[0]:-$0}")/scripts/fetch_weather.py"
```

如果上面的相對路徑不行，用 skill 安裝路徑：

```bash
uv run <skill-directory>/scripts/fetch_weather.py
```

腳本先輸出 RPG 風格的讀取進度條（折疊預覽只會看到「⏳ 正在讀取天氣資料...」），最後一行才是 JSON。

支援 `WEATHER_CITY` 環境變數或傳參數覆蓋位置（如 `uv run ... Tokyo`）。
支援多城市查詢（如 `uv run ... 台北 高雄` 或 `WEATHER_CITY="台北,高雄"`）。
純 Python（只用標準庫），零暫存檔，並行 API 呼叫，輸出一行 JSON。

## 怎麼回應

1. 跑腳本取得 JSON
2. **讀 `references/prompt-guide.md`**（語氣、時段、台灣用語）
3. 逐行輸出 `display.rendered`（是陣列，每個元素一行，不要放進 code block）
4. 根據 `data` + prompt-guide 寫對話框
5. 穿搭：參考 `references/outfit-guide.md`，自然融入聊天
6. 多天預報：只在連假/天氣劇變時帶出（不要每次都報）
7. 卡片 + 對話框一起輸出

## 輸出格式（RPG 風格）

### 狀態面板

`display.rendered` 是陣列，每個元素是卡片的一行。**逐行輸出，每行獨立一行，不要放進 code block**。
多城市時，每個城市的 `rendered` 各輸出一張，中間空一行。

### 對話框

聊天文字用 `▶` 開頭，自然分段：

```
▶ lancetw，週日晚上了，吃飽沒？

  外面涼涼的，散步不錯。
  空氣霧霧的，口罩帶著吧。
  明天週一天氣差不多，安心收假。
```

規則：
- 第一句用 `▶` 開頭（像 RPG 對話指標）
- 後續段落縮排兩格，不加 `▶`
- 3-5 句，每 1-2 句換一行

**如果腳本失敗**（網路斷、API 掛、timeout）：不要假裝有資料。直接跟使用者說「抱歉，天氣資料暫時抓不到，等一下再試試。」

## 參考文件

| 文件 | 內容 | 何時讀 |
|------|------|--------|
| `references/prompt-guide.md` | 語氣、時段關心、台灣用語、數字規則 | **每次都讀** |
| `references/data-fields.md` | JSON 欄位說明、活用時機 | 不確定欄位意思時讀 |
| `references/outfit-guide.md` | 穿搭建議對照表 | 需要穿搭建議時讀 |
| `assets/examples.md` | 12 種情境範例 | 想看範例時讀 |
