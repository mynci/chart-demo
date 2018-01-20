# -*- coding: utf-8 -*-
import os
from datetime import datetime
import matplotlib.pyplot as plt

import pandas as pd
from .base import DataReaderBase, SimpleLoggingObject


'''
Code example written by Stephen Kemp.

This code was written from scratch with an arbitrary time limit of ~8 hours.
A lot more can and would be done to fully generalise and extend the code,
Hopefully this demonstrates the intent and my coding style sufficiently.

I have not put any formal docstring comments in as they are so dependant on the 
documentation system that might be used. Therefore I have simply put a simple 
explanation of what all but the most trivial methods do.

This is a simple demonstration of a tool that can:
- Read an input data file or URL into a pandas dataframe
- Perform some grouping and aggregation of the dataset
- Display a graph of the grouped and filtered data

This has been written and tested using XUbuntu 16.04 and Python 3.5.

It requires the following libraries:

pyqt5
pyqtgraph
pandas

All availible via pip, eg:
sudo pip install pyqt5 pyqtgraph pandas 

'''


class DataFileReader(DataReaderBase):

    def __init__(self, file_path):

        # initialise the base class
        super(DataFileReader, self).__init__()

        self.file_path = None
        self.file_dir = None
        self.file_name = None

        self.set_file_path(file_path)

        return None

    def build_qa_data(self):
        '''
        Build some basic QA data
        '''
        qa_data = {}

        qa_data["file_path"] = self.file_path
        qa_data["file_dir"] = self.file_dir
        qa_data["file_name"] = self.file_name

        ctime = os.path.getctime(self.file_path)
        qa_data["created"] = datetime.fromtimestamp(ctime)

        mtime = os.path.getmtime(self.file_path)
        qa_data["modified"] = datetime.fromtimestamp(mtime)

        qa_data["filesize_bytes"] = os.path.getsize(self.file_path)

        self.qa_data = qa_data

        return None

    def set_file_path(self, file_path):
        '''
        Handle a changed file path
        '''
        # expand any path shorthand, e.g. ~
        if file_path is not None:
            file_path = os.path.expanduser(file_path)

            if not os.path.isfile(file_path):
                msg = "File {} is not a readable file".format(file_path)
                raise IOError(msg)

            # store the full path and the directory and file name
            self.file_path = file_path
            self.file_dir, self.file_name = os.path.split(file_path)

            self.build_qa_data()

        return None


class PandasFileReader(DataFileReader):
    '''
    Subclass of the standard file reader, this is specialised to use pandas CSV
    reading routines. In some future, extended framework new file reading
    methods could be implemented at this level of the object hierarchy
    '''
    def __init__(self, file_path, *args, **kwargs):

        super(PandasFileReader, self).__init__(file_path)

        self.args = args
        self.kwargs = kwargs
        self.data = None

        return None

    def read(self):

        self.data = pd.read_csv(self.file_path, *self.args, **self.kwargs)

        return None

    def get_dataframe(self):

        if not isinstance(self.data, pd.DataFrame):
            self.read()

        return self.data

