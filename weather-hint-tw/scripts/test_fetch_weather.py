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


if __name__ == '__main__':
    unittest.main()
