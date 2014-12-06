import socket
import urllib2
from pyparsing import Word, alphas
from pyhocon.config_parser import ConfigParser


class ConfigFactory(object):
    @staticmethod
    def parseFile(filename):
        """
        Parse file
        :param filename: filename
        :type filename: basestring
        :return: Config object
        :type return: Config
        """
        with open(filename, 'r') as fd:
            content = fd.read()
            return ConfigFactory.parseString(content)

    @staticmethod
    def parseURL(url, timeout=None):
        """
        Parse URL
        :param url: url to parse
        :type url: basestring
        :return: Config object
        :type return: Config
        """
        socket_timeout = socket._GLOBAL_DEFAULT_TIMEOUT if timeout is None else timeout
        fd = urllib2.urlopen(url, timeout=socket_timeout)
        content = fd.read()
        return ConfigFactory.parseString(content)

    @staticmethod
    def parseString(content):
        """
        Parse URL
        :param url: url to parse
        :type url: basestring
        :return: Config object
        :type return: Config
        """
        return ConfigParser().parse(content)
