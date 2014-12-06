class ConfigException(Exception):

    def __init__(self, message, key_path):
        super(ConfigException, self).__init__(message)
        self._key_path = key_path
