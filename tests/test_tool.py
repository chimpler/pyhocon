import tempfile
import pytest
from pyhocon import ConfigFactory
from pyhocon.tool import HOCONConverter


class TestHOCONConverter(object):
    CONFIG_STRING = """
            a = {b: 1}
            b = [1, 2]
            c = 1
            d = "a"
            e = \"\"\"1
                2
                3\"\"\"
            f = true
            g = []
            h = null
            i = {}
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
              "f": true,
              "g": [],
              "h": null,
              "i": {}
            }
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
            f: true
            g: []
            h: None
            i:
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
            f = true
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

    def _test_convert(self, input, expected_output, format):
        with tempfile.NamedTemporaryFile('w') as fdin:
            fdin.write(input)
            fdin.flush()
            with tempfile.NamedTemporaryFile('r') as fdout:
                HOCONConverter.convert(fdin.name, fdout.name, format)
                with open(fdout.name) as fdi:
                    converted = fdi.read()
                    assert [line.strip() for line in expected_output.split('\n') if line.strip()]\
                        == [line.strip() for line in converted.split('\n') if line.strip()]

    def test_convert(self):
        self._test_convert(TestHOCONConverter.CONFIG_STRING, TestHOCONConverter.EXPECTED_JSON, 'json')
        self._test_convert(TestHOCONConverter.CONFIG_STRING, TestHOCONConverter.EXPECTED_YAML, 'yaml')
        self._test_convert(TestHOCONConverter.CONFIG_STRING, TestHOCONConverter.EXPECTED_PROPERTIES, 'properties')

    def test_invalid_format(self):
        with pytest.raises(Exception):
            self._test_convert(TestHOCONConverter.CONFIG_STRING, TestHOCONConverter.EXPECTED_PROPERTIES, 'invalid')
