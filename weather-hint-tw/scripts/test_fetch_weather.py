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


if __name__ == '__main__':
    unittest.main()
