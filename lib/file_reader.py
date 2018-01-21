# -*- coding: utf-8 -*-
import os
from datetime import datetime

import pandas as pd

from .base import DataReaderBase


'''
File reading specific objects. Includes a base file reader DataFileReader
that deals with basic path handling and builds QA data.

The PandasFileReader is a specialisation of the file reader that will read a
file to a DataFrame

It is intended that the parent DataReaderBase could be branched off into, say,
a URL reader or other non-file data source.

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
        Build some basic QA data, there is a lot more we could add here
        depending on the use case.
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
    methods could be implemented at this level of the object hierarchy.
    '''
    def __init__(self, file_path, *args, **kwargs):

        super(PandasFileReader, self).__init__(file_path)

        self.args = args
        self.kwargs = kwargs
        self.data = None

        return None

    def read(self):
        # get pandas to perform the read, note we do not check the args or
        # kwargs but Pandas will report any errors. Future versions may check
        # these upfront or allow more specific access to arguments of read_csv
        self.data = pd.read_csv(self.file_path, *self.args, **self.kwargs)

        return None

    def get_dataframe(self):
        # Only parse the file if we need to.
        if not isinstance(self.data, pd.DataFrame):
            self.read()

        return self.data

