# weather-hint-tw 改進實作計畫

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 升級 weather-hint-tw — 穩定性、多城市、7 天預報、穿搭建議、對話品質、測試

**Architecture:** 維持單檔腳本，提取函式加 `if __name__ == '__main__'` 使其可測試。新增 outfit-guide.md，擴充 prompt-guide.md 和 examples.md。純 unittest 測試。

**Tech Stack:** Python stdlib, unittest, Open-Meteo API, geojs.io

**Design doc:** `docs/plans/2026-03-22-weather-hint-tw-improvements-design.md`

---

### Task 1: 重命名腳本 + 加 __name__ guard

**目的：** 讓測試能 import 腳本內的函式

**Files:**
- Rename: `weather-hint-tw/scripts/fetch-weather.py` → `weather-hint-tw/scripts/fetch_weather.py`
- Modify: `weather-hint-tw/SKILL.md`

**Step 1: 重命名檔案**

```bash
cd /Users/lancetw/Documents/vibe_workspace/skills/lancetw/skills
mv weather-hint-tw/scripts/fetch-weather.py weather-hint-tw/scripts/fetch_weather.py
```

**Step 2: 包裝 main()**

把 `# === Step 1` 之後的所有頂層程式碼包進 `def main():` 裡，檔案尾加：

```python
if __name__ == '__main__':
    main()
```

保留 `fetch()`, `ri()`, `rain_info()` 在 module level（可被 import）。

**Step 3: 提取 helper 函式**

從 inline 邏輯提取為可測試函式：

```python
def get_wind_desc(wind):
    """風況描述"""
    if wind >= 30: return '風大'
    if wind >= 15: return '微風'
    return '無風'

def get_weather_emoji(code):
    """天氣代碼 → emoji"""
    EMOJI = {0:'☀️',1:'🌤️',2:'⛅',3:'⛅',45:'🌫️',48:'🌫️',
             51:'🌦️',53:'🌦️',55:'🌦️',61:'🌧️',63:'🌧️',65:'🌧️',
             71:'🌨️',73:'🌨️',75:'🌨️',80:'🌧️',81:'🌧️',82:'🌧️',95:'⛈️'}
    return EMOJI.get(code, '🌤️')
```

在 `main()` 裡用 `get_wind_desc(wind)` 和 `get_weather_emoji(code)` 取代 inline 版本。

**Step 4: 更新 SKILL.md**

```diff
-uv run "$(dirname -- "${BASH_SOURCE[0]:-}")/scripts/fetch-weather.py"
+uv run "$(dirname -- "${BASH_SOURCE[0]:-}")/scripts/fetch_weather.py"
```

```diff
-uv run <skill-directory>/scripts/fetch-weather.py
+uv run <skill-directory>/scripts/fetch_weather.py
```

**Step 5: 驗證腳本正常執行**

```bash
uv run weather-hint-tw/scripts/fetch_weather.py
```

Expected: 一行 JSON 輸出，格式與之前相同

**Step 6: Commit**

```bash
git add weather-hint-tw/scripts/fetch_weather.py weather-hint-tw/SKILL.md
git commit -m "refactor: rename fetch-weather.py, extract functions for testability"
```

---

### Task 2: fetch() retry 邏輯（TDD）

**Files:**
- Create: `weather-hint-tw/scripts/test_fetch_weather.py`
- Modify: `weather-hint-tw/scripts/fetch_weather.py`

**Step 1: 寫失敗測試**

```python
#!/usr/bin/env python3
"""weather-hint-tw 單元測試"""
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import URLError
import importlib.util, os, sys

# import module
_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('fetch_weather', os.path.join(_dir, 'fetch_weather.py'))
fw = importlib.util.module_from_spec(_spec)
# 只載入函式，不執行 main
sys.modules['fetch_weather'] = fw
_spec.loader.exec_module(fw)


class TestFetch(unittest.TestCase):
    @patch('fetch_weather.urlopen')
    def test_retry_succeeds_on_second_attempt(self, mock_urlopen):
        """第一次失敗、第二次成功 → 回傳資料"""
        resp = MagicMock()
        resp.read.return_value = b'{"ok": true}'
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.side_effect = [URLError('timeout'), resp]
        result = fw.fetch('http://example.com')
        self.assertEqual(result, {'ok': True})
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch('fetch_weather.urlopen')
    def test_retry_exhausted_returns_empty(self, mock_urlopen):
        """全部失敗 → return {}"""
        mock_urlopen.side_effect = URLError('down')
        result = fw.fetch('http://example.com')
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()
```

**Step 2: 執行測試確認失敗**

```bash
uv run python -m pytest weather-hint-tw/scripts/test_fetch_weather.py -v 2>/dev/null || \
uv run python -m unittest weather-hint-tw.scripts.test_fetch_weather -v
```

Expected: FAIL（目前 fetch() 沒有 retry）

**Step 3: 實作 retry**

修改 `fetch_weather.py` 的 `fetch()`:

```python
import time as _time

TIMEOUT = int(os.environ.get('WEATHER_TIMEOUT', '5'))

def fetch(url, retries=2, delay=1):
    for attempt in range(retries):
        try:
            req = Request(url, headers={'User-Agent': 'weather-hint-tw/1.0'})
            with urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read())
        except (URLError, TimeoutError, ValueError) as e:
            if attempt < retries - 1:
                _time.sleep(delay)
                print(f'[warn] retry {attempt+1}: {url[:60]}…', file=sys.stderr)
            else:
                print(f'[warn] failed: {url[:60]}… ({e})', file=sys.stderr)
    return {}
```

**Step 4: 執行測試確認通過**

```bash
uv run python -m unittest weather-hint-tw/scripts/test_fetch_weather.py -v
```

Expected: 2 tests PASS

**Step 5: Commit**

```bash
git add weather-hint-tw/scripts/fetch_weather.py weather-hint-tw/scripts/test_fetch_weather.py
git commit -m "feat: add retry logic to fetch() with tests"
```

---

### Task 3: 既有函式測試

**Files:**
- Modify: `weather-hint-tw/scripts/test_fetch_weather.py`

**Step 1: 加 ri() / rain_info() / wind / emoji 測試**

在 test 檔案新增：

```python
class TestHelpers(unittest.TestCase):
    def test_ri_normal(self):
        self.assertEqual(fw.ri(24.6), '25')
        self.assertEqual(fw.ri(24.4), '24')

    def test_ri_string(self):
        self.assertEqual(fw.ri('18.7'), '19')

    def test_ri_invalid(self):
        self.assertEqual(fw.ri('?'), '?')
        self.assertEqual(fw.ri(None), '?')

    def test_rain_info_with_rain(self):
        icon, desc = fw.rain_info(30, '☀️')
        self.assertEqual(icon, '☂️')
        self.assertEqual(desc, '可能下雨')

    def test_rain_info_no_rain(self):
        icon, desc = fw.rain_info(0, '⛅')
        self.assertEqual(icon, '⛅')
        self.assertEqual(desc, '不會下雨')

    def test_get_wind_desc(self):
        self.assertEqual(fw.get_wind_desc(0), '無風')
        self.assertEqual(fw.get_wind_desc(14.9), '無風')
        self.assertEqual(fw.get_wind_desc(15), '微風')
        self.assertEqual(fw.get_wind_desc(29.9), '微風')
        self.assertEqual(fw.get_wind_desc(30), '風大')
        self.assertEqual(fw.get_wind_desc(50), '風大')

    def test_get_weather_emoji_known(self):
        self.assertEqual(fw.get_weather_emoji(0), '☀️')
        self.assertEqual(fw.get_weather_emoji(61), '🌧️')
        self.assertEqual(fw.get_weather_emoji(95), '⛈️')

    def test_get_weather_emoji_unknown(self):
        self.assertEqual(fw.get_weather_emoji(999), '🌤️')
```

**Step 2: 執行全部測試**

```bash
uv run python -m unittest weather-hint-tw/scripts/test_fetch_weather.py -v
```

Expected: 所有測試 PASS

**Step 3: Commit**

```bash
git add weather-hint-tw/scripts/test_fetch_weather.py
git commit -m "test: add unit tests for ri, rain_info, wind_desc, emoji"
```

---

### Task 4: 7 天預報（TDD）

**Files:**
- Modify: `weather-hint-tw/scripts/test_fetch_weather.py`
- Modify: `weather-hint-tw/scripts/fetch_weather.py`

**Step 1: 寫失敗測試**

```python
class TestForecast(unittest.TestCase):
    def test_build_forecast_normal(self):
        daily = {
            'time': ['2026-03-22','2026-03-23','2026-03-24','2026-03-25',
                     '2026-03-26','2026-03-27','2026-03-28'],
            'temperature_2m_max': [28, 27, 26, 25, 24, 23, 22],
            'temperature_2m_min': [18, 17, 16, 15, 14, 13, 12],
            'precipitation_probability_max': [0, 10, 20, 30, 40, 50, 60],
            'weather_code': [0, 1, 2, 3, 61, 63, 95],
        }
        result = fw.build_forecast(daily)
        self.assertEqual(len(result), 5)  # day 2-6 (後天~第7天)
        self.assertEqual(result[0]['day'], '03/24(二)')
        self.assertEqual(result[0]['max'], 26)
        self.assertEqual(result[0]['rain'], 20)

    def test_build_forecast_short_data(self):
        daily = {
            'time': ['2026-03-22', '2026-03-23'],
            'temperature_2m_max': [28, 27],
            'temperature_2m_min': [18, 17],
            'precipitation_probability_max': [0, 10],
            'weather_code': [0, 1],
        }
        result = fw.build_forecast(daily)
        self.assertEqual(len(result), 0)  # 不夠天數 → 空

    def test_build_forecast_empty(self):
        result = fw.build_forecast({})
        self.assertEqual(result, [])
```

**Step 2: 執行測試確認失敗**

Expected: `AttributeError: module has no attribute 'build_forecast'`

**Step 3: 實作 build_forecast()**

在 `fetch_weather.py` 加入：

```python
def build_forecast(daily, start=2, end=7):
    """後天到第 7 天的每日摘要"""
    WEEKDAYS = '一二三四五六日'
    result = []
    times = daily.get('time', [])
    maxs = daily.get('temperature_2m_max', [])
    mins = daily.get('temperature_2m_min', [])
    rains = daily.get('precipitation_probability_max', [])
    codes = daily.get('weather_code', [])
    for i in range(start, min(end, len(times))):
        dt = datetime.strptime(times[i], '%Y-%m-%d')
        result.append({
            'day': f'{dt.strftime("%m/%d")}({WEEKDAYS[dt.weekday()]})',
            'max': maxs[i] if i < len(maxs) else '?',
            'min': mins[i] if i < len(mins) else '?',
            'rain': rains[i] if i < len(rains) else 0,
            'code': codes[i] if i < len(codes) else 0,
        })
    return result
```

**Step 4: 修改 API 參數**

在 `main()` 中，把所有 `forecast_days=2` 改成 `forecast_days=7`。

**Step 5: 在 main() 中呼叫 build_forecast 並加入 output**

在建構 `output['data']` 時加：

```python
'forecast': build_forecast(dy),
```

**Step 6: 執行全部測試**

```bash
uv run python -m unittest weather-hint-tw/scripts/test_fetch_weather.py -v
```

Expected: 全部 PASS

**Step 7: 手動驗證**

```bash
uv run weather-hint-tw/scripts/fetch_weather.py | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d['data']['forecast'], indent=2, ensure_ascii=False))"
```

Expected: 5 天的 forecast 陣列

**Step 8: Commit**

```bash
git add weather-hint-tw/scripts/fetch_weather.py weather-hint-tw/scripts/test_fetch_weather.py
git commit -m "feat: add 7-day forecast with build_forecast()"
```

---

### Task 5: 多城市支援（TDD）

**Files:**
- Modify: `weather-hint-tw/scripts/test_fetch_weather.py`
- Modify: `weather-hint-tw/scripts/fetch_weather.py`

**Step 1: 寫失敗測試**

```python
class TestMultiCity(unittest.TestCase):
    def test_parse_cities_from_argv(self):
        result = fw.parse_cities(['台北', '高雄'], '')
        self.assertEqual(result, ['台北', '高雄'])

    def test_parse_cities_from_env(self):
        result = fw.parse_cities([], '台北,高雄,新竹')
        self.assertEqual(result, ['台北', '高雄', '新竹'])

    def test_parse_cities_env_with_spaces(self):
        result = fw.parse_cities([], ' 台北 , 高雄 ')
        self.assertEqual(result, ['台北', '高雄'])

    def test_parse_cities_single(self):
        result = fw.parse_cities(['台中'], '')
        self.assertEqual(result, ['台中'])

    def test_parse_cities_empty(self):
        result = fw.parse_cities([], '')
        self.assertEqual(result, [])

    def test_parse_cities_env_overrides_argv(self):
        """環境變數優先"""
        result = fw.parse_cities(['台北'], '高雄')
        self.assertEqual(result, ['高雄'])
```

**Step 2: 執行測試確認失敗**

Expected: `AttributeError: module has no attribute 'parse_cities'`

**Step 3: 實作 parse_cities()**

```python
def parse_cities(argv, env_val):
    """解析城市列表。env 優先於 argv"""
    if env_val:
        return [c.strip() for c in env_val.split(',') if c.strip()]
    return list(argv) if argv else []
```

**Step 4: 重構 main() 支援多城市**

核心邏輯：

```python
def main():
    env_city = os.environ.get('WEATHER_CITY', '')
    argv_cities = sys.argv[1:]
    cities = parse_cities(argv_cities, env_city)

    if len(cities) <= 1:
        # 單城市：原有邏輯（向後相容）
        city_override = cities[0] if cities else ''
        result = fetch_single_city(city_override)
        print('\n\n\n' + json.dumps(result, ensure_ascii=False))
    else:
        # 多城市
        results = []
        for c in cities:
            results.append(fetch_single_city(c))
        print('\n\n\n' + json.dumps({'cities': results}, ensure_ascii=False))
```

把目前 `main()` 中從 `# === Step 1` 到 output 建構的邏輯包進 `fetch_single_city(city_override='')` 函式。

**Step 5: 執行全部測試**

```bash
uv run python -m unittest weather-hint-tw/scripts/test_fetch_weather.py -v
```

Expected: 全部 PASS

**Step 6: 手動驗證多城市**

```bash
uv run weather-hint-tw/scripts/fetch_weather.py 台北 高雄
```

Expected: `{"cities": [{...}, {...}]}` 格式

**Step 7: Commit**

```bash
git add weather-hint-tw/scripts/fetch_weather.py weather-hint-tw/scripts/test_fetch_weather.py
git commit -m "feat: add multi-city support via argv and WEATHER_CITY env"
```

---

### Task 6: 假日解析測試

**Files:**
- Modify: `weather-hint-tw/scripts/test_fetch_weather.py`
- Modify: `weather-hint-tw/scripts/fetch_weather.py`

**Step 1: 提取假日解析為函式**

從 `main()` 中把假日邏輯提取成：

```python
def parse_holidays(holidays, now):
    """解析未來 3 天假日資訊"""
    days = []
    if not isinstance(holidays, list):
        return days
    for i in range(3):
        dt = (now + timedelta(days=i)).strftime('%Y%m%d')
        for hol in holidays:
            if hol.get('date') == dt:
                desc = hol.get('description', '')
                is_h = hol.get('isHoliday', False)
                week = hol.get('week', '?')
                tag = desc if desc else ('holiday' if is_h else 'workday')
                days.append(f'{dt}({week}) {tag}')
                break
    return days
```

**Step 2: 寫測試**

```python
from datetime import datetime, timedelta

class TestHolidays(unittest.TestCase):
    def test_parse_holidays_normal(self):
        now = datetime(2026, 3, 22)
        holidays = [
            {'date': '20260322', 'isHoliday': True, 'week': '日', 'description': ''},
            {'date': '20260323', 'isHoliday': False, 'week': '一', 'description': ''},
        ]
        result = fw.parse_holidays(holidays, now)
        self.assertEqual(result[0], '20260322(日) holiday')
        self.assertEqual(result[1], '20260323(一) workday')

    def test_parse_holidays_with_name(self):
        now = datetime(2026, 6, 25)
        holidays = [
            {'date': '20260625', 'isHoliday': True, 'week': '四', 'description': '端午節'},
        ]
        result = fw.parse_holidays(holidays, now)
        self.assertIn('端午節', result[0])

    def test_parse_holidays_empty(self):
        result = fw.parse_holidays([], datetime(2026, 1, 1))
        self.assertEqual(result, [])

    def test_parse_holidays_not_list(self):
        result = fw.parse_holidays({}, datetime(2026, 1, 1))
        self.assertEqual(result, [])
```

**Step 3: 執行測試**

```bash
uv run python -m unittest weather-hint-tw/scripts/test_fetch_weather.py -v
```

Expected: 全部 PASS

**Step 4: Commit**

```bash
git add weather-hint-tw/scripts/fetch_weather.py weather-hint-tw/scripts/test_fetch_weather.py
git commit -m "refactor: extract parse_holidays() with tests"
```

---

### Task 7: 建立 outfit-guide.md

**Files:**
- Create: `weather-hint-tw/references/outfit-guide.md`

**Step 1: 寫穿搭對照表**

```markdown
# 穿搭建議指引

根據 `data` 裡的溫度、天氣、風速等資料，自然地融入聊天建議。

## 溫度 × 天氣 對照

| 溫度 | 晴/多雲 | 雨天 |
|------|---------|------|
| ≥32° | 短袖短褲、防曬、帽子、墨鏡 | 短袖 + 薄防水外套 |
| 26-31° | T-shirt、薄長褲 | T-shirt + 傘，鞋選防水的 |
| 20-25° | 薄長袖，或短袖加薄外套 | 薄外套 + 傘，別穿布鞋 |
| 15-19° | 外套必備、長褲 | 防水外套、長褲、防水鞋 |
| 10-14° | 厚外套，考慮圍巾 | 厚防水外套、保暖配件 |
| <10° | 大衣或羽絨、手套圍巾 | 全副武裝，注意路滑 |

## 修正因子

| 條件 | 調整 |
|------|------|
| 風大（≥30 km/h） | 外套升一級，帽子可能被吹走別戴 |
| 溫差 >10° | 洋蔥式穿法，帶外套出門 |
| 濕度 >80% | 避免厚棉質（不容易乾），選透氣材質 |
| UV ≥6 | 加防曬、帽子、墨鏡 |

## 語氣規則

- 穿搭建議融入聊天，不條列
- ✅ 「今天薄外套就夠了，中午熱可以脫掉」
- ✅ 「下午會下雨，鞋子穿防水的比較好」
- ❌ 「建議穿著：短袖 + 薄外套 + 長褲 + 防水鞋」
- 不要每次都提穿搭，天氣普通時可以省略
- 極端天氣（很冷、很熱、大雨）才特別強調
```

**Step 2: Commit**

```bash
git add weather-hint-tw/references/outfit-guide.md
git commit -m "feat: add outfit-guide.md for clothing suggestions"
```

---

### Task 8: 擴充 prompt-guide.md

**Files:**
- Modify: `weather-hint-tw/references/prompt-guide.md`

**Step 1: 新增以下段落（追加在現有內容之後）**

新增段落：

1. **情境矩陣**（天氣 × 時段交叉範例）

```markdown
## 情境矩陣

常見的天氣 × 時段組合，提供切入參考：

| 時段 | 晴熱 | 涼爽舒適 | 下雨 | 寒流 |
|------|------|---------|------|------|
| 清晨 | 「今天會很曬，早點出門比較涼」 | 「早起好舒服，外面涼涼的」 | 「下雨天早起辛苦，傘帶著」 | 「好冷喔，多穿一點再出門」 |
| 上午 | 「太陽已經很大了，水壺帶著」 | 「天氣不錯，午休可以出去走走」 | 「外面在下雨，待辦公室也好」 | 「冷氣團來了，辦公室有暖氣嗎」 |
| 下午 | 「下午最曬，能不出去就不出去」 | 「下午了，外面蠻舒服的」 | 「雨還在下，等下出門記得傘」 | 「越來越冷了，早點回家吧」 |
| 晚上 | 「晚上涼下來了，出去走走不錯」 | 「晚上微涼，很適合散步」 | 「雨聲蠻助眠的，早點休息」 | 「冷到不想出門，窩著也好」 |
| 深夜 | 「夜深了，明天也會很熱，早點睡」 | 「今晚涼涼的，睡覺很舒服」 | 「還在下雨，別出門了，早點休息」 | 「這麼冷還沒睡？棉被蓋好」 |
```

2. **變化技巧**

```markdown
## 變化技巧

避免每次回應都長得一樣。

### 開場輪換

不要每次都「辛苦了」。以下開場隨機選用，同一天內不重複：

- 關心型：「忙了一天了吧？」「還在加班啊？」「吃飯了沒？」
- 觀察型：「外面剛下了一場雨」「太陽好大」「風有點大」
- 時間型：「週五了！」「連假倒數」「早安～」
- 直接型：直接講天氣，不加問候（偶爾用）

### 結尾輪換

不要每次都「早點休息」：

- 「明天見」「週末愉快」「好好享受」
- 「加油，撐過今天」「喝杯熱的吧」
- 直接結束，不加結尾語（偶爾用）

### 結構變化

- 有時先講天氣再關心，有時反過來
- 有時 3 句就好，不需要每次都 5 句
- 穿搭建議不是每次都要，天氣普通就省略
```

3. **多城市語氣**

```markdown
## 多城市比較

查多個城市時，用差異帶出，不要逐城市重複同樣結構。

- ✅ 「台北比高雄涼了 5 度，記得多帶件外套」
- ✅ 「新竹風超大，台北還好」
- ✅ 「兩邊都不會下雨，放心」
- ❌ 逐城市各寫一段一模一樣的結構
- ❌ 「台北：24度，多雲。高雄：29度，晴。」

重點放在對使用者有用的差異（溫差、有沒有雨、要不要多帶東西）。
```

4. **多天預報語氣**

```markdown
## 多天預報

data 裡有 `forecast`（後天到第 7 天），但不要每次都報。

### 什麼時候提

- 連假前 → 「連假幾天天氣都不錯」「週日可能會下雨，安排室內活動」
- 天氣將有劇變 → 「週三開始轉涼，先準備厚外套」
- 使用者主動問 → 完整但自然地講

### 怎麼提

- ✅ 「後面幾天都是好天氣」
- ✅ 「週三有一波雨，趁明天先把衣服曬一曬」
- ❌ 「週三 22°/16°，降雨 40%；週四 20°/14°，降雨 60%」
```

5. **穿搭融入**

```markdown
## 穿搭建議

參考 `references/outfit-guide.md` 的對照表，自然融入聊天。

- 根據溫度 × 天氣查表，用口語講
- 修正因子（風、溫差、濕度、UV）有符合就帶一句
- 天氣普通（20-28°晴）可以不提穿搭
- 極端天氣一定要提
```

**Step 2: Commit**

```bash
git add weather-hint-tw/references/prompt-guide.md
git commit -m "feat: expand prompt-guide with variation, multi-city, forecast, outfit sections"
```

---

### Task 9: 擴充 examples.md

**Files:**
- Modify: `weather-hint-tw/assets/examples.md`

**Step 1: 在現有 4 個範例之後，新增 8 個情境**

新增以下情境（每個都要有 card + 聊天 + 穿搭融入示範）：

1. **深夜加班 — 微涼**
2. **清晨出門 — 有雨**
3. **極端高溫（>36°）— 正午**
4. **寒流（<10°）— 早上**
5. **颱風警報 — 下午**
6. **連假第一天 — 晴天**
7. **多城市比較 — 台北 vs 高雄**
8. **溫差極大（>12°）— 傍晚**

每個範例格式同現有範例：code block 卡片 + 3-5 句聊天。

**Step 2: 擴充「不要這樣寫」反例**

新增反例：
- 每次都「辛苦了」開頭
- 逐城市重複同樣結構
- 條列式穿搭建議
- 每次都報 7 天預報

**Step 3: Commit**

```bash
git add weather-hint-tw/assets/examples.md
git commit -m "feat: expand examples from 4 to 12 scenarios"
```

---

### Task 10: 更新 data-fields.md 和 SKILL.md

**Files:**
- Modify: `weather-hint-tw/references/data-fields.md`
- Modify: `weather-hint-tw/SKILL.md`

**Step 1: data-fields.md 新增欄位說明**

在 `data` 表格新增：

| 欄位 | 說明 | 活用時機 |
|------|------|---------|
| `forecast` | 後天~第 7 天每日摘要 | 連假/天氣劇變時自然帶出 |

多城市格式說明：
- 單城市：`{card, data}` 不變
- 多城市：`{"cities": [{card, data}, ...]}`

**Step 2: SKILL.md 更新用法**

在使用說明加：

```markdown
支援多城市查詢：

```bash
uv run <skill-directory>/scripts/fetch_weather.py 台北 高雄
```

或用環境變數：

```bash
WEATHER_CITY="台北,高雄" uv run <skill-directory>/scripts/fetch_weather.py
```
```

在「怎麼回應」加：
- 穿搭：參考 `references/outfit-guide.md`
- 多天預報：只在連假/劇變時帶出

在參考文件表格加 `outfit-guide.md`。

**Step 3: Commit**

```bash
git add weather-hint-tw/references/data-fields.md weather-hint-tw/SKILL.md
git commit -m "docs: update data-fields and SKILL.md for new features"
```

---

### Task 11: 全部測試 + 最終驗證

**Step 1: 跑全部測試**

```bash
uv run python -m unittest weather-hint-tw/scripts/test_fetch_weather.py -v
```

Expected: 全部 PASS

**Step 2: 手動驗證單城市**

```bash
uv run weather-hint-tw/scripts/fetch_weather.py
```

**Step 3: 手動驗證多城市**

```bash
uv run weather-hint-tw/scripts/fetch_weather.py 台北 高雄
```

**Step 4: 驗證 forecast 欄位存在**

```bash
uv run weather-hint-tw/scripts/fetch_weather.py | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'forecast' in d['data']; print('OK:', len(d['data']['forecast']), 'days')"
```
