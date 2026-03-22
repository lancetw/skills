#!/usr/bin/env python3
"""天氣提醒 — 取得資料 + 格式化輸出，零暫存。"""
import json, os, random, sys, time as _time, unicodedata
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote

TIMEOUT = int(os.environ.get('WEATHER_TIMEOUT', '5'))

# 台灣城市中文 → 英文（Open-Meteo geocoding 不支援中文搜尋）
TW_CITY_MAP = {
    '台北': 'Taipei', '臺北': 'Taipei', '台北市': 'Taipei', '臺北市': 'Taipei',
    '新北': 'New Taipei', '新北市': 'New Taipei',
    '桃園': 'Taoyuan', '桃園市': 'Taoyuan',
    '台中': 'Taichung', '臺中': 'Taichung', '台中市': 'Taichung', '臺中市': 'Taichung',
    '台南': 'Tainan', '臺南': 'Tainan', '台南市': 'Tainan', '臺南市': 'Tainan',
    '高雄': 'Kaohsiung', '高雄市': 'Kaohsiung',
    '基隆': 'Keelung', '基隆市': 'Keelung',
    '新竹': 'Hsinchu', '新竹市': 'Hsinchu', '新竹縣': 'Hsinchu County',
    '苗栗': 'Miaoli', '苗栗縣': 'Miaoli',
    '彰化': 'Changhua', '彰化縣': 'Changhua',
    '南投': 'Nantou', '南投縣': 'Nantou',
    '雲林': 'Yunlin', '雲林縣': 'Yunlin',
    '嘉義': 'Chiayi', '嘉義市': 'Chiayi', '嘉義縣': 'Chiayi County',
    '屏東': 'Pingtung', '屏東縣': 'Pingtung',
    '宜蘭': 'Yilan', '宜蘭縣': 'Yilan',
    '花蓮': 'Hualien', '花蓮縣': 'Hualien',
    '台東': 'Taitung', '臺東': 'Taitung', '台東縣': 'Taitung', '臺東縣': 'Taitung',
    '澎湖': 'Penghu', '澎湖縣': 'Penghu',
    '金門': 'Kinmen', '金門縣': 'Kinmen',
    '連江': 'Lienchiang', '連江縣': 'Lienchiang', '馬祖': 'Matsu',
}

EMOJI = {0:'☀️',1:'🌤️',2:'⛅',3:'⛅',45:'🌫️',48:'🌫️',51:'🌦️',53:'🌦️',55:'🌦️',
         61:'🌧️',63:'🌧️',65:'🌧️',71:'🌨️',73:'🌨️',75:'🌨️',80:'🌧️',81:'🌧️',82:'🌧️',95:'⛈️'}

_SAGE_PREFIX = ['告知', '解答', '確認', '受理', '解析開始']
_SAGE_ACTION = [
    '氣象情報解析中', '取得天候資料中', '收集氣象情報',
    '天候情報檢索中', '環境資訊解析中', '存取氣象資料庫',
    '啟動技能『天氣預報』', '氣象數據讀取中',
]


def fetch(url, retries=2, delay=1):
    for attempt in range(retries):
        try:
            req = Request(url, headers={'User-Agent': 'weather-hint-tw/1.0'})
            with urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read())
        except (URLError, ValueError) as e:
            if attempt < retries - 1:
                print(f'[warn] retry {attempt+1}: {url[:60]}…', file=sys.stderr)
                _time.sleep(delay)
            else:
                print(f'[warn] failed: {url[:60]}… ({e})', file=sys.stderr)
    return {}


def geocode_nominatim(query):
    """Nominatim fallback — 支援中文區/鄉/鎮名（南港區、霧台鄉…）"""
    q = quote(f'{query},台灣')
    url = f'https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1&countrycodes=tw'
    data = fetch(url)
    if isinstance(data, list) and data:
        return str(data[0].get('lat', '')), str(data[0].get('lon', ''))
    return '', ''


def ri(v):
    try: return str(round(float(v)))
    except: return '?'

def rain_info(pct, weather_emoji):
    if pct >= 60:
        return '☂️', f'降雨 {pct}%'
    if pct >= 30:
        return '🌂', f'降雨 {pct}%'
    if pct > 0:
        return weather_emoji, f'降雨 {pct}%'
    return weather_emoji, '不會下雨'

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


def get_wind_desc(wind):
    """風況描述"""
    if wind >= 30: return '風大'
    if wind >= 15: return '微風'
    return '無風'

def get_weather_emoji(code):
    """天氣代碼 → emoji"""
    return EMOJI.get(code, '🌤️')


def _char_width(c):
    """單一字元在 terminal 的顯示寬度"""
    cp = ord(c)
    # Zero-width: variation selectors, ZWJ, skin tone modifiers
    if cp in (0xFE0E, 0xFE0F, 0x200D) or 0x1F3FB <= cp <= 0x1F3FF:
        return 0
    # Emoji (U+1F000+) — 大部分 terminal 渲染為 2 cells
    if cp >= 0x1F000:
        return 2
    # Misc symbols 常見 emoji（☀⛅☂⛈…）
    if 0x2600 <= cp <= 0x27BF or 0x2300 <= cp <= 0x23FF:
        return 2
    # CJK & fullwidth
    eaw = unicodedata.east_asian_width(c)
    return 2 if eaw in ('F', 'W') else 1


def visual_width(s):
    """字串在 terminal 的顯示寬度"""
    return sum(_char_width(c) for c in s)


def render_card(display):
    """將 display dict 渲染成 RPG 風格卡片（含右邊框）"""
    keys = ['地點', '溫度', '天氣', '今日', '明日', '提醒']
    lines = [display[k] for k in keys if k in display]
    if not lines:
        return ''
    widths = [visual_width(line) for line in lines]
    max_w = max(widths)

    result = []
    # Header: ╔═ {title} ═══...╗
    title_w = widths[0]
    result.append(f'╔═ {lines[0]} {"═" * (max_w - title_w)}╗')
    # Content: ║ {line}   ...║
    for line, w in zip(lines[1:], widths[1:]):
        result.append(f'║ {line}{" " * (max_w - w + 2)}║')
    # Footer: ╚═══...╝
    result.append(f'╚{"═" * (max_w + 3)}╝')
    return '\n'.join(result)


def compute_hints(time_str, temp, feel, t_max, t_min, tm_max, hourly_str, forecast, hourly_data=None):
    """預先計算 AI 回應用的衍生提示，減少 AI 推理負擔"""
    hints = {}

    # 時段
    try:
        hour = int(time_str.split('T')[1][:2])
    except Exception:
        hour = 12
    periods = [
        (5, '清晨'), (7, '早上'), (9, '上午'), (12, '中午'),
        (14, '下午'), (17, '傍晚'), (19, '晚上'), (22, '深夜'),
    ]
    hints['period'] = '深夜'
    for start, name in periods:
        if hour < start:
            break
        hints['period'] = name

    # 今日溫差
    try:
        hints['temp_range'] = round(float(t_max) - float(t_min), 1)
    except Exception:
        hints['temp_range'] = 0

    # 體感差異（正=體感更熱，負=體感更冷）
    try:
        hints['feel_diff'] = round(float(feel) - float(temp), 1)
    except Exception:
        hints['feel_diff'] = 0

    # 未來 6 小時會不會下雨（任一小時 ≥30%）
    try:
        probs = [int(e.split(':')[-1].replace('%', '')) for e in hourly_str.split()]
        hints['rain_soon'] = any(p >= 30 for p in probs)
    except Exception:
        hints['rain_soon'] = False

    # 明天趨勢
    try:
        diff = float(tm_max) - float(t_max)
        if diff >= 3:
            hints['tomorrow_trend'] = '明顯升溫'
        elif diff <= -3:
            hints['tomorrow_trend'] = '明顯降溫'
        else:
            hints['tomorrow_trend'] = '差不多'
    except Exception:
        hints['tomorrow_trend'] = '差不多'

    # 未來幾天劇變（供判斷是否帶出多天預報）
    changes = []
    if isinstance(forecast, list):
        for day in forecast:
            rain = day.get('rain', 0)
            if isinstance(rain, (int, float)) and rain >= 50:
                changes.append(f'{day.get("day", "?")} 有雨')
            try:
                if float(day.get('min', 20)) <= float(t_min) - 5:
                    changes.append(f'{day.get("day", "?")} 轉涼')
                elif float(day.get('max', 25)) >= float(t_max) + 5:
                    changes.append(f'{day.get("day", "?")} 變熱')
            except Exception:
                pass
    hints['forecast_change'] = changes if changes else None

    # 最高溫時段（台灣氣象常識：中午～下午 1 點）
    hints['peak_temp_period'] = '中午'

    # 明天各時段溫度（從逐時資料算出）
    hints['tomorrow_morning_temp'] = None  # 07-09 平均
    hints['tomorrow_noon_temp'] = None     # 12-14 平均
    if hourly_data and 'time' in hourly_data and 'temperature_2m' in hourly_data:
        try:
            today = time_str.split('T')[0]
            tomorrow = (datetime.strptime(today, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            tm_temps = {}
            for t, v in zip(hourly_data['time'], hourly_data['temperature_2m']):
                if t.startswith(tomorrow):
                    h = int(t.split('T')[1][:2])
                    tm_temps[h] = v
            morning = [tm_temps[h] for h in (7, 8, 9) if h in tm_temps]
            if morning:
                hints['tomorrow_morning_temp'] = round(sum(morning) / len(morning))
            noon = [tm_temps[h] for h in (12, 13, 14) if h in tm_temps]
            if noon:
                hints['tomorrow_noon_temp'] = round(sum(noon) / len(noon))
        except Exception:
            pass

    return hints


def parse_holidays(holidays, now):
    """解析未來 3 天假日資訊"""
    days = []
    if not isinstance(holidays, list):
        return days
    labels = ['今天', '明天', '後天']
    for i in range(3):
        dt = (now + timedelta(days=i)).strftime('%Y%m%d')
        for hol in holidays:
            if hol.get('date') == dt:
                desc = hol.get('description', '')
                is_h = hol.get('isHoliday', False)
                week = hol.get('week', '?')
                status = '放假' if is_h else '上班'
                if desc:
                    days.append(f'{labels[i]} 週{week} {desc}({status})')
                else:
                    days.append(f'{labels[i]} 週{week} {status}')
                break
    return days


def parse_cities(argv, env_val):
    """解析城市列表。env 優先於 argv"""
    if env_val:
        return [c.strip() for c in env_val.split(',') if c.strip()]
    return list(argv) if argv else []


def fetch_single_city(city_override=''):
    """取得單一城市天氣，回傳 output dict（不 print）"""
    lat, lon, city = '', '', ''
    city_display = ''  # 使用者輸入的原始名稱

    if city_override:
        city_display = city_override
        # 中文城市名 → 英文（geocoding API 不支援中文）
        city = TW_CITY_MAP.get(city_override, city_override)
    else:
        geo = fetch('https://get.geojs.io/v1/ip/geo.json')
        city = geo.get('city', '')
        lat = str(geo.get('latitude', ''))
        lon = str(geo.get('longitude', ''))

        if not city:
            # 時區 fallback
            try:
                tz = os.readlink('/etc/localtime').split('zoneinfo/')[-1].split('/')[-1]
                city = tz
            except:
                city = 'Taipei'

    # === Step 2: 並行 API ===
    year = datetime.now().strftime('%Y')
    urls = {
        'geo': f'https://geocoding-api.open-meteo.com/v1/search?name={quote(city)}&count=1&language=zh-TW',
        'holiday': f'https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{year}.json',
    }
    if lat and lon:
        urls['weather'] = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,precipitation,uv_index&hourly=precipitation_probability,weather_code,temperature_2m&forecast_hours=42&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code,sunrise,sunset&forecast_days=7&timezone=auto'
        urls['aqi'] = f'https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm2_5,pm10,us_aqi&timezone=auto'

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {k: pool.submit(fetch, v) for k, v in urls.items()}
        data = {k: f.result() for k, f in futures.items()}

    # 沒有經緯度時從 geocoding 取得再查
    if not lat or not lon:
        results = data.get('geo', {}).get('results', [{}])
        if results:
            lat = str(results[0].get('latitude', ''))
            lon = str(results[0].get('longitude', ''))
        # Open-Meteo 查不到 → Nominatim fallback（區/鄉/鎮名）
        if not lat or not lon:
            lat, lon = geocode_nominatim(city_display or city)
        if not lat or not lon:
            print(f'[error] 找不到「{city_display or city}」的位置資料', file=sys.stderr)
        if lat and lon:
            with ThreadPoolExecutor(max_workers=2) as pool:
                wf = pool.submit(fetch, f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,precipitation,uv_index&hourly=precipitation_probability,weather_code,temperature_2m&forecast_hours=42&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code,sunrise,sunset&forecast_days=7&timezone=auto')
                af = pool.submit(fetch, f'https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm2_5,pm10,us_aqi&timezone=auto')
                data['weather'] = wf.result()
                data['aqi'] = af.result()

    # === 解析 ===
    r = data.get('geo', {}).get('results', [{}])[0]
    # name 和 admin2 哪個是中文不一定，自動挑含中文字的
    geo_name = r.get('admin2', '') or r.get('name', '') or city
    for _f in ('admin2', 'name'):
        _v = r.get(_f, '')
        if _v and any('\u4e00' <= c <= '\u9fff' for c in _v):
            geo_name = _v
            break
    city_tw = (city_display or geo_name).replace('臺', '台')

    c = data.get('weather', {}).get('current', {})
    temp = c.get('temperature_2m', '?')
    feel = c.get('apparent_temperature', '?')
    hum = c.get('relative_humidity_2m', '?')
    code = c.get('weather_code', 0)
    wind = c.get('wind_speed_10m', 0)
    uv = c.get('uv_index', 0)
    time_str = c.get('time', '?')

    w_emoji = get_weather_emoji(code)
    wind_desc = get_wind_desc(wind)

    dy = data.get('weather', {}).get('daily', {})
    t_max = dy.get('temperature_2m_max', ['?','?'])[0]
    t_min = dy.get('temperature_2m_min', ['?','?'])[0]
    t_rain = dy.get('precipitation_probability_max', [0,0])[0]
    tm_max = dy.get('temperature_2m_max', ['?','?'])[1]
    tm_min = dy.get('temperature_2m_min', ['?','?'])[1]
    tm_rain = dy.get('precipitation_probability_max', [0,0])[1]
    sunset = dy.get('sunset', ['?','?'])[0]
    sunrise = dy.get('sunrise', ['?','?'])[0]
    sunset_s = sunset.split('T')[1][:5] if 'T' in str(sunset) else '?'
    sunrise_s = sunrise.split('T')[1][:5] if 'T' in str(sunrise) else '?'

    ac = data.get('aqi', {}).get('current', {})
    aqi_val = ac.get('us_aqi', 0)
    pm25 = ac.get('pm2_5', 0)

    # === 卡片資料（供 AI 排版用）===
    # 風
    line2_parts = [f'濕度 {hum}%', wind_desc]
    try:
        now_h = int(time_str.split('T')[1][:2])
        if abs(now_h - int(sunset_s[:2])) <= 1:
            line2_parts.append(f'日落 {sunset_s}')
        if 5 <= now_h <= 7:
            line2_parts.append(f'日出 {sunrise_s}')
    except: pass

    # 空氣/UV
    alerts = []
    if aqi_val and int(aqi_val) > 100:
        alerts.append('空氣不太好')
    if uv and float(uv) >= 6:
        alerts.append('紫外線很強')

    # === 卡片資料 ===
    t_code = dy.get('weather_code', [0,0])[0]
    t_emoji = get_weather_emoji(t_code)
    tm_code = dy.get('weather_code', [0,0])[1]
    tm_emoji_raw = get_weather_emoji(tm_code)
    t_icon, t_rain_desc = rain_info(t_rain, t_emoji)
    tm_icon, tm_rain_desc = rain_info(tm_rain, tm_emoji_raw)

    # === 逐時 ===
    h = data.get('weather', {}).get('hourly', {})
    times = h.get('time', [])
    rain_probs = h.get('precipitation_probability', [])
    hourly = []
    for i in range(len(times)):
        hr = times[i].split('T')[1][:5] if 'T' in times[i] else times[i]
        hourly.append(f'{hr}:{rain_probs[i]}%')

    # === 假日 ===
    holidays = data.get('holiday', [])
    days = parse_holidays(holidays, datetime.now())

    # === 逐時字串（供 hints 用）===
    hourly_str = ' '.join(hourly)

    # === 預算提示 ===
    forecast_data = build_forecast(dy)
    hourly_temps_data = {'time': times, 'temperature_2m': h.get('temperature_2m', [])}
    hints = compute_hints(time_str, temp, feel, t_max, t_min, tm_max, hourly_str, forecast_data,
                          hourly_data=hourly_temps_data)

    # === 輸出 dict ===
    output = {
        'display': {
            '地點': f'{w_emoji} {city_tw}',
            '溫度': f'{ri(temp)}°C（體感 {ri(feel)}°C）',
            '天氣': f'💧 {"  ".join(line2_parts)}',
            '今日': f'{t_icon} {ri(t_max)}°~{ri(t_min)}°  {t_rain_desc}',
            '明日': f'{tm_icon} {ri(tm_max)}°~{ri(tm_min)}°  {tm_rain_desc}',
        },
        'data': {
            'city': city_tw, 'time': time_str,
            'temp': temp, 'feel': feel, 'hum': hum,
            'wind': wind, 'uv': uv,
            'hourly': hourly_str,
            'today_high': t_max, 'today_low': t_min, 'today_rain': t_rain,
            'sunrise': sunrise_s, 'sunset': sunset_s,
            'tomorrow_high': tm_max, 'tomorrow_low': tm_min, 'tomorrow_rain': tm_rain,
            'aqi': aqi_val, 'pm25': pm25,
            'days': days,
            'forecast': forecast_data,
            'hints': hints,
        }
    }
    if alerts:
        output['display']['提醒'] = f'😷 {"  ".join(alerts)}'
    output['display']['rendered'] = render_card(output['display'])
    return output


def main():
    env_city = os.environ.get('WEATHER_CITY', '')
    argv_cities = sys.argv[1:]
    cities = parse_cities(argv_cities, env_city)

    if len(cities) <= 1:
        city_override = cities[0] if cities else ''
        result = fetch_single_city(city_override)
    else:
        results = []
        for c in cities:
            results.append(fetch_single_city(c))
        result = {'cities': results}

    print('\n')
    print(f'⏳ {random.choice(_SAGE_PREFIX)}。{random.choice(_SAGE_ACTION)}...')
    print('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
