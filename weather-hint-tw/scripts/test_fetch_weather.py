#!/usr/bin/env python3
"""weather-hint-tw unit tests"""
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import URLError
from datetime import datetime
import importlib.util, os, sys

# import module without executing main()
_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('fetch_weather', os.path.join(_dir, 'fetch_weather.py'))
fw = importlib.util.module_from_spec(_spec)
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
        result = fw.fetch('http://example.com', delay=0)
        self.assertEqual(result, {'ok': True})
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch('fetch_weather.urlopen')
    def test_retry_exhausted_returns_empty(self, mock_urlopen):
        """全部失敗 → return {}"""
        mock_urlopen.side_effect = URLError('down')
        result = fw.fetch('http://example.com', delay=0)
        self.assertEqual(result, {})


class TestHelpers(unittest.TestCase):
    def test_ri_normal(self):
        self.assertEqual(fw.ri(24.6), '25')
        self.assertEqual(fw.ri(24.4), '24')

    def test_ri_string(self):
        self.assertEqual(fw.ri('18.7'), '19')

    def test_ri_invalid(self):
        self.assertEqual(fw.ri('?'), '?')
        self.assertEqual(fw.ri(None), '?')

    def test_rain_info_heavy(self):
        icon, desc = fw.rain_info(60, '☀️')
        self.assertEqual(icon, '☂️')
        self.assertEqual(desc, '降雨 60%')

    def test_rain_info_possible(self):
        icon, desc = fw.rain_info(30, '☀️')
        self.assertEqual(icon, '🌂')
        self.assertEqual(desc, '降雨 30%')

    def test_rain_info_low(self):
        icon, desc = fw.rain_info(10, '⛅')
        self.assertEqual(icon, '⛅')
        self.assertEqual(desc, '降雨 10%')

    def test_rain_info_zero(self):
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


class TestHolidays(unittest.TestCase):
    def test_parse_holidays_normal(self):
        now = datetime(2026, 3, 22)
        holidays = [
            {'date': '20260322', 'isHoliday': True, 'week': '日', 'description': ''},
            {'date': '20260323', 'isHoliday': False, 'week': '一', 'description': ''},
        ]
        result = fw.parse_holidays(holidays, now)
        self.assertEqual(result[0], '今天 週日 放假')
        self.assertEqual(result[1], '明天 週一 上班')

    def test_parse_holidays_with_name(self):
        now = datetime(2026, 6, 25)
        holidays = [
            {'date': '20260625', 'isHoliday': True, 'week': '四', 'description': '端午節'},
        ]
        result = fw.parse_holidays(holidays, now)
        self.assertEqual(result[0], '今天 週四 端午節(放假)')

    def test_parse_holidays_makeup_workday(self):
        now = datetime(2026, 6, 20)
        holidays = [
            {'date': '20260620', 'isHoliday': False, 'week': '六', 'description': '補行上班日'},
        ]
        result = fw.parse_holidays(holidays, now)
        self.assertEqual(result[0], '今天 週六 補行上班日(上班)')

    def test_parse_holidays_empty(self):
        result = fw.parse_holidays([], datetime(2026, 1, 1))
        self.assertEqual(result, [])

    def test_parse_holidays_not_list(self):
        result = fw.parse_holidays({}, datetime(2026, 1, 1))
        self.assertEqual(result, [])


class TestComputeHints(unittest.TestCase):
    def test_period_morning(self):
        h = fw.compute_hints('2026-03-22T08:30', 20, 21, 28, 18, 27, '', [])
        self.assertEqual(h['period'], '早上')

    def test_period_evening(self):
        h = fw.compute_hints('2026-03-22T18:30', 20, 21, 28, 18, 27, '', [])
        self.assertEqual(h['period'], '傍晚')

    def test_period_late_night(self):
        h = fw.compute_hints('2026-03-22T23:00', 20, 21, 28, 18, 27, '', [])
        self.assertEqual(h['period'], '深夜')

    def test_period_early_morning(self):
        h = fw.compute_hints('2026-03-22T03:00', 20, 21, 28, 18, 27, '', [])
        self.assertEqual(h['period'], '深夜')

    def test_period_all_slots(self):
        cases = [
            ('04:00', '深夜'), ('05:30', '清晨'), ('07:30', '早上'),
            ('10:00', '上午'), ('13:00', '中午'), ('15:00', '下午'),
            ('18:00', '傍晚'), ('20:00', '晚上'), ('23:00', '深夜'),
        ]
        for time_part, expected in cases:
            h = fw.compute_hints(f'2026-03-22T{time_part}', 20, 21, 28, 18, 27, '', [])
            self.assertEqual(h['period'], expected, f'{time_part} should be {expected}')

    def test_temp_range(self):
        h = fw.compute_hints('2026-03-22T12:00', 20, 21, 30, 18, 27, '', [])
        self.assertEqual(h['temp_range'], 12.0)

    def test_feel_diff_hotter(self):
        h = fw.compute_hints('2026-03-22T12:00', 20, 25, 28, 18, 27, '', [])
        self.assertEqual(h['feel_diff'], 5.0)

    def test_feel_diff_colder(self):
        h = fw.compute_hints('2026-03-22T12:00', 20, 17, 28, 18, 27, '', [])
        self.assertEqual(h['feel_diff'], -3.0)

    def test_rain_soon_true(self):
        hourly = '18:00:10% 19:00:50% 20:00:60% 21:00:30% 22:00:0% 23:00:0%'
        h = fw.compute_hints('2026-03-22T18:00', 20, 21, 28, 18, 27, hourly, [])
        self.assertTrue(h['rain_soon'])

    def test_rain_soon_false(self):
        hourly = '18:00:0% 19:00:10% 20:00:5% 21:00:0% 22:00:0% 23:00:0%'
        h = fw.compute_hints('2026-03-22T18:00', 20, 21, 28, 18, 27, hourly, [])
        self.assertFalse(h['rain_soon'])

    def test_tomorrow_trend_warming(self):
        h = fw.compute_hints('2026-03-22T12:00', 20, 21, 25, 18, 30, '', [])
        self.assertEqual(h['tomorrow_trend'], '明顯升溫')

    def test_tomorrow_trend_cooling(self):
        h = fw.compute_hints('2026-03-22T12:00', 20, 21, 30, 18, 25, '', [])
        self.assertEqual(h['tomorrow_trend'], '明顯降溫')

    def test_tomorrow_trend_stable(self):
        h = fw.compute_hints('2026-03-22T12:00', 20, 21, 28, 18, 27, '', [])
        self.assertEqual(h['tomorrow_trend'], '差不多')

    def test_forecast_change_rain(self):
        forecast = [
            {'day': '03/25(三)', 'max': 28, 'min': 18, 'rain': 70, 'code': 61},
            {'day': '03/26(四)', 'max': 27, 'min': 17, 'rain': 10, 'code': 2},
        ]
        h = fw.compute_hints('2026-03-22T12:00', 20, 21, 28, 18, 27, '', forecast)
        self.assertIn('03/25(三) 有雨', h['forecast_change'])

    def test_forecast_change_cold(self):
        forecast = [
            {'day': '03/26(四)', 'max': 20, 'min': 10, 'rain': 0, 'code': 2},
        ]
        h = fw.compute_hints('2026-03-22T12:00', 20, 21, 28, 18, 27, '', forecast)
        self.assertIn('03/26(四) 轉涼', h['forecast_change'])

    def test_forecast_change_none(self):
        forecast = [
            {'day': '03/25(三)', 'max': 28, 'min': 18, 'rain': 10, 'code': 2},
        ]
        h = fw.compute_hints('2026-03-22T12:00', 20, 21, 28, 18, 27, '', forecast)
        self.assertIsNone(h['forecast_change'])

    def test_invalid_time(self):
        h = fw.compute_hints('bad', 20, 21, 28, 18, 27, '', [])
        self.assertEqual(h['period'], '中午')  # fallback hour=12

    def test_invalid_temps(self):
        h = fw.compute_hints('2026-03-22T12:00', '?', '?', '?', '?', '?', '', [])
        self.assertEqual(h['temp_range'], 0)
        self.assertEqual(h['feel_diff'], 0)
        self.assertEqual(h['tomorrow_trend'], '差不多')


if __name__ == '__main__':
    unittest.main()
