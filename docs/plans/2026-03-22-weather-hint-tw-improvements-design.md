# weather-hint-tw 改進設計

日期：2026-03-22
方案：B — 腳本升級 + 文件強化

## §1 腳本穩定性

- `fetch()` 加 retry（最多 2 次，間隔 1 秒）
- 明確 catch `URLError` / `TimeoutError` / `ValueError`
- 失敗 stderr 印 warning，不影響 JSON 輸出
- `TIMEOUT` 可由 `WEATHER_TIMEOUT` 環境變數覆蓋
- 不加 cache、不加外部依賴

## §2 多城市

- 輸入：多個 argv（`uv run ... 台北 高雄`）或 `WEATHER_CITY="台北,高雄"`
- 輸出：單城市維持現有結構（向後相容），多城市 `{"cities": [{card, data}, ...]}`
- 語氣：用比較語氣，不逐城市重複

## §3 多天預報

- `forecast_days=2` → `forecast_days=7`
- card 不變（只顯示今日/明日）
- data 新增 `forecast` 陣列：後天~第 7 天，每天 `{day, max, min, rain, code}`
- 預設不提多天預報，只在連假/天氣劇變/使用者主動問時帶出

## §4 穿搭建議

- 新增 `references/outfit-guide.md` 穿搭對照表
- 溫度區間 × 天氣條件 → 穿搭建議
- 修正因子：風大、溫差大、高濕、高 UV
- 融入聊天，不條列

## §5 對話品質

### prompt-guide.md 擴充

- 情境矩陣（天氣 × 時段 交叉指引）
- 變化技巧：10+ 種開場模板、結尾變化
- 多城市比較語氣指引
- 多天預報語氣指引
- 穿搭融入規則

### examples.md 從 4 → 12+

新增：深夜加班、清晨出門、極端高溫(>36°)、寒流(<10°)、颱風/暴雨、連假第一天、多城市比較、溫差極大(>12°)，每個附穿搭示範

## §6 測試

- `scripts/test_fetch_weather.py`，純 unittest，零外部依賴
- Mock `urlopen`，不打真實 API
- 測試項目：retry 邏輯、ri()、rain_info()、wind_desc 邊界值、emoji mapping、多城市解析、forecast 陣列、假日解析
- 不測 AI 聊天文字
- 執行：`uv run python -m unittest scripts/test_fetch_weather.py`
