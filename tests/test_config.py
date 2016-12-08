import unittest
from mock import Mock, MagicMock
from glogcli.utils import extract_fields_from_format, get_color_option


class UtilsTestCase(unittest.TestCase):

    def test_get_color_with_color_option_enabled(self):
        self.assertTrue(get_color_option(self.mock_config('true', True), 'format_name', no_color=False))
        self.assertTrue(get_color_option(self.mock_config('', False), 'format_name', no_color=False))

    def test_get_color_with_no_color_option_disabled(self):
        self.assertFalse(get_color_option(self.mock_config('true', True), 'format_name', no_color=True))
        self.assertFalse(get_color_option(self.mock_config('false', True), 'format_name', no_color=False))
        self.assertFalse(get_color_option(self.mock_config('false', True), 'format_name', no_color=True))
        self.assertFalse(get_color_option(self.mock_config('False', True), 'format_name', no_color=True))
        self.assertFalse(get_color_option(self.mock_config('NO', True), 'format_name', no_color=True))

    def mock_config(self, get_return=None, has_option_return=None):
        mock = MagicMock()
        mock.get = Mock(return_value=get_return)
        mock.has_option = Mock(return_value=has_option_return)
        return mock
