import tempfile
import pytest
from pyhocon import ConfigFactory
from pyhocon.tool import HOCONConverter


class TestHOCONConverter(object):
    CONFIG_STRING = u"""
            a = {b: 1}
            b = [1, 2]
            c = 1
            d = "a"
            e = \"\"\"1
                2
                3\"\"\"
            f1 = true
            f2 = false
            g = []
            h = null
            i = {}
            "a.b" = 2
        """

    CONFIG = ConfigFactory.parse_string(CONFIG_STRING)

    EXPECTED_JSON = \
        """
            {
              "a": {
                "b": 1
              },
              "b": [
                1,
                2
              ],
              "c": 1,
              "d": "a",
              "e": "1\\n                2\\n                3",
              "f1": true,
              "f2": false,
              "g": [],
              "h": null,
              "i": {},
              "a.b": 2
            }
        """

    EXPECTED_HOCON = \
        """
              a {
                b = 1
              }
              b = [
                1
                2
              ]
              c = 1
              d = "a"
              e = \"\"\"1\n                2\n                3\"\"\"
              f1 = true
              f2 = false
              g = []
              h = null
              i {}
              "a.b" = 2
        """

    EXPECTED_YAML = \
        """
            a:
              b: 1
            b:
              - 1
              - 2
            c: 1
            d: a
            e: |
             1
                            2
                        3
            f1: true
            f2: false
            g: []
            h: None
            i:
            a.b: 2
        """

    EXPECTED_PROPERTIES = \
        """
            a.b = 1
            b.0 = 1
            b.1 = 2
            c = 1
            d = a
            e = 1\\
                            2\\
                        3
            f1 = true
            f2 = false
            a.b = 2
        """

    def test_to_json(self):
        converted = HOCONConverter.to_json(TestHOCONConverter.CONFIG)
        assert [line.strip() for line in TestHOCONConverter.EXPECTED_JSON.split('\n') if line.strip()]\
            == [line.strip() for line in converted.split('\n') if line.strip()]

    def test_to_yaml(self):
        converted = HOCONConverter.to_yaml(TestHOCONConverter.CONFIG)
        assert [line.strip() for line in TestHOCONConverter.EXPECTED_YAML.split('\n') if line.strip()]\
            == [line.strip() for line in converted.split('\n') if line.strip()]

    def test_to_properties(self):
        converted = HOCONConverter.to_properties(TestHOCONConverter.CONFIG)
        assert [line.strip() for line in TestHOCONConverter.EXPECTED_PROPERTIES.split('\n') if line.strip()]\
            == [line.strip() for line in converted.split('\n') if line.strip()]

    def test_to_hocon(self):
        converted = HOCONConverter.to_hocon(TestHOCONConverter.CONFIG)
        assert [line.strip() for line in TestHOCONConverter.EXPECTED_HOCON.split('\n') if line.strip()]\
            == [line.strip() for line in converted.split('\n') if line.strip()]

    def _test_convert_from_file(self, input, expected_output, format):
        with tempfile.NamedTemporaryFile('w') as fdin:
            fdin.write(input)
            fdin.flush()
            with tempfile.NamedTemporaryFile('r') as fdout:
                HOCONConverter.convert_from_file(fdin.name, fdout.name, format)
                with open(fdout.name) as fdi:
                    converted = fdi.read()
                    assert [line.strip() for line in expected_output.split('\n') if line.strip()]\
                        == [line.strip() for line in converted.split('\n') if line.strip()]

    def test_convert_from_file(self):
        self._test_convert_from_file(TestHOCONConverter.CONFIG_STRING, TestHOCONConverter.EXPECTED_JSON, 'json')
        self._test_convert_from_file(TestHOCONConverter.CONFIG_STRING, TestHOCONConverter.EXPECTED_YAML, 'yaml')
        self._test_convert_from_file(TestHOCONConverter.CONFIG_STRING, TestHOCONConverter.EXPECTED_PROPERTIES, 'properties')
        self._test_convert_from_file(TestHOCONConverter.CONFIG_STRING, TestHOCONConverter.EXPECTED_HOCON, 'hocon')

    def test_invalid_format(self):
        with pytest.raises(Exception):
            self._test_convert_from_file(TestHOCONConverter.CONFIG_STRING, TestHOCONConverter.EXPECTED_PROPERTIES, 'invalid')
