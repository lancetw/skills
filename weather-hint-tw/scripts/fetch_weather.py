#!/usr/bin/env python3
"""天氣提醒 — 取得資料 + 格式化輸出，零暫存。"""
import json, os, sys, time as _time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request
from urllib.error import URLError

TIMEOUT = int(os.environ.get('WEATHER_TIMEOUT', '5'))

EMOJI = {0:'☀️',1:'🌤️',2:'⛅',3:'⛅',45:'🌫️',48:'🌫️',51:'🌦️',53:'🌦️',55:'🌦️',
         61:'🌧️',63:'🌧️',65:'🌧️',71:'🌨️',73:'🌨️',75:'🌨️',80:'🌧️',81:'🌧️',82:'🌧️',95:'⛈️'}

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

def ri(v):
    try: return str(round(float(v)))
    except: return '?'

def rain_info(pct, weather_emoji):
    if pct > 0:
        return '☂️', '可能下雨'
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


def main():
    # === Step 1: 位置 ===
    city_override = os.environ.get('WEATHER_CITY', '') or (sys.argv[1] if len(sys.argv) > 1 else '')
    lat, lon, city = '', '', ''

    if city_override:
        city = city_override
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
        'geo': f'https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=zh-TW',
        'holiday': f'https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{year}.json',
    }
    if lat and lon:
        urls['weather'] = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,precipitation,uv_index&hourly=precipitation_probability,weather_code&forecast_hours=6&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code,sunrise,sunset&forecast_days=7&timezone=auto'
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
        if lat and lon:
            with ThreadPoolExecutor(max_workers=2) as pool:
                wf = pool.submit(fetch, f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,precipitation,uv_index&hourly=precipitation_probability,weather_code&forecast_hours=6&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code,sunrise,sunset&forecast_days=7&timezone=auto')
                af = pool.submit(fetch, f'https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm2_5,pm10,us_aqi&timezone=auto')
                data['weather'] = wf.result()
                data['aqi'] = af.result()

    # === 解析 ===
    r = data.get('geo', {}).get('results', [{}])[0]
    city_tw = r.get('admin2', r.get('name', city)).replace('臺', '台')

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
    days = []
    if isinstance(holidays, list):
        now = datetime.now()
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

    # === 全部輸出為一行 JSON（避免 CLI 劇透）===
    output = {
        'card': {
            'city': f'{w_emoji} {city_tw}',
            'temp': f'{ri(temp)}°C（體感 {ri(feel)}°C）',
            'detail': f'💧 {"  ".join(line2_parts)}',
            'today': f'{t_icon} 今日 {ri(t_max)}°~{ri(t_min)}°  {t_rain_desc}',
            'tomorrow': f'{tm_icon} 明日 {ri(tm_max)}°~{ri(tm_min)}°  {tm_rain_desc}',
        },
        'data': {
            'city': city_tw, 'time': time_str,
            'temp': temp, 'feel': feel, 'hum': hum, 'code': code,
            'wind': wind, 'uv': uv,
            'hourly': ' '.join(hourly),
            'today': f'max{t_max}/min{t_min} sunset{sunset_s}',
            'tomorrow': f'max{tm_max}/min{tm_min} rain{tm_rain}%',
            'aqi': aqi_val, 'pm25': pm25,
            'days': days,
            'forecast': build_forecast(dy),
        }
    }
    if alerts:
        output['card']['alert'] = f'😷 {"  ".join(alerts)}'
    print('\n\n\n' + json.dumps(output, ensure_ascii=False))


if __name__ == '__main__':
    main()
