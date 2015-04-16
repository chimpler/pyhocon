from pyhocon import ConfigFactory
from pyhocon.tool import HOCONConverter


class TestHOCONConverter(object):
    CONFIG = ConfigFactory.parse_string(
        """
            a = {b: 1}
            b = [1, 2]
            c = 1
            d = "a"
            e = \"\"\"1
                2
            3\"\"\"
        """
    )

    def test_to_json(self):
        expected = \
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
              "e": "1\\n                2\\n            3"
            }
            """

        converted = HOCONConverter.to_json(TestHOCONConverter.CONFIG)
        assert [line.strip() for line in expected.split('\n') if line.strip()] == [line.strip() for line in converted.split('\n') if line.strip()]

    def test_to_yaml(self):
        expected = \
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
            """
        converted = HOCONConverter.to_yaml(TestHOCONConverter.CONFIG)
        assert [line.strip() for line in expected.split('\n') if line.strip()] == [line.strip() for line in converted.split('\n') if line.strip()]

    def test_to_properties(self):
        expected = \
            """
            a.b = 1
            b.0 = 1
            b.1 = 2
            c = 1
            d = a
            e = 1\\
                            2\\
                        3
            """
        converted = HOCONConverter.to_properties(TestHOCONConverter.CONFIG)
        assert [line.strip() for line in expected.split('\n') if line.strip()] == [line.strip() for line in converted.split('\n') if line.strip()]
