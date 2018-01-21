# -*- coding: utf-8 -*-
import logging

'''
This contains the very basic objects that are used throughout the tools
'''


class SimpleLoggingObject(object):
    '''
    Very basic class to use for all derived classes - just adds logging methods
    info, warn, error and exception.
    '''
    def __init__(self):
        return None

    def info(self, msg):
        logging.info(msg)
        return None

    def warn(self, msg):
        logging.warn(msg)
        return None

    def error(self, msg):
        logging.error(msg)
        return None

    def exception(self, msg):
        logging.exception(msg)
        return None


class DataReaderBase(SimpleLoggingObject):
    '''
    Base data reading object, this is mostly for convenience in case I need
    to add features to it later.
    '''

    def __init__(self):
        self.data = None
        return None

    def read(self):
        # subclasses must re implement this method
        msg = "Method read() must be overridden in subclass"
        raise NotImplementedError(msg)

        return None

