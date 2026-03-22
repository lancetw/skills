#!/usr/bin/env python3
"""weather-hint-tw unit tests"""
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import URLError
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


if __name__ == '__main__':
    unittest.main()
