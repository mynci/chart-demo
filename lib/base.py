# -*- coding: utf-8 -*-
import os
import logging
from datetime import datetime
import matplotlib.pyplot as plt

import pyqtgraph as pg
import pandas as pd

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
- Perform some grouping and filtering on the data set
- Display a graph of the grouped and filtered data

This has been written and tested using XUbuntu 16.04 and Python 3.5.

It requires the following libraries:

pyqt5
pyqtgraph
pandas

All availible via pip, eg:
sudo pip install pyqt5 pyqtgraph pandas 

'''


def is_numeric(test_str):

    result = True

    try:
        float(test_str)
    except ValueError:

        result = False

    return result


def all_numeric(val_list):

    result = all([is_numeric(x) for x in val_list])

    return result


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
        # subclasses must override this method
        msg = "Method read() must be overridden in subclass"
        raise NotImplementedError(msg)

        return None


class DataFileReader(DataReaderBase):

    def __init__(self, file_path):

        # initialise the base class
        super(DataFileReader, self).__init__()

        self.file_path = None
        self.file_dir = None
        self.file_name = None

        self.set_file_path(file_path)

        self.build_qa_data()

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
        file_path = os.path.expanduser(file_path)

        if not os.path.isfile(file_path):
            msg = "File {} is not a readable file".format(file_path)
            raise IOError(msg)

        # store the full path and the directory and file name
        self.file_path = file_path
        self.file_dir, self.file_name = os.path.split(file_path)

        return None


class PandasFileReader(DataFileReader):
    '''
    Subclass of the standard file reader, this is specialised to use pandas CSV 
    reading routines.
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


class DataFilter(object):

    def __init__(self, data):

        self.data = data

        return None

    def filter(self):

        return self.data


class DataGrouper(SimpleLoggingObject):

    def __init__(self, data=None, groupby_cols=None, apply_funct=None):

        self.data = data
        self.groupby_cols = groupby_cols
        self.apply_funct = apply_funct
        self.grouped_data = None
        self.result_data = None
        self.invalid_cols = None
        self.agg_args = None
        return None

    def set_groupby_cols(self, columns):

        if self.groupby_cols != columns:
            self.groupby_cols = columns
            self.grouped_data = None
            self.result_data = None

        return None

    def set_data(self, data):

        refresh_data = False

        if not isinstance(self.data, pd.DataFrame):
            refresh_data = True
        else:
            # we need to protect this with a type check as dataframes are
            # fussy about comparison types
            if self.data != data:
                refresh_data = True

        if refresh_data:
            self.data = data
            self.grouped_data = None
            self.result_data = None

        return None

    def set_apply_funct(self, apply_funct):

        if self.apply_funct != apply_funct:
            self.apply_funct = apply_funct
            self.result_data = None

            if self.agg_args is not None:
                msg = ("Apply function set, but an apply function "
                       "was already set removing the Aggregation srguments")
                self.warn(msg)
                self.agg_args = None

        return None

    def set_agg_args(self, agg_args):

        if self.agg_args != agg_args:
            self.agg_args = agg_args
            self.result_data = None

            if self.apply_funct is not None:
                msg = ("Aggregation arguments are set, but an apply function "
                       "was already set removing the apply function")
                self.warn(msg)
                self.apply_funct = None

        return None

    def groupby_cols_valid(self):
        '''
        Check that the columns specified in the groupby_cols argument are in
        the dataframe that is stored.
        '''
        result = False

        if self.groupby_cols is not None and isinstance(self.data, pd.DataFrame):
            self.invalid_cols = [col for col in self.groupby_cols
                                 if col not in self.data.columns]
            result = (len(self.invalid_cols) == 0)

        return result

    def __call__(self, data=None, groupby_cols=None, apply_funct=None,
                 agg_args=None):
        '''
        Allow the object instance to be called like a function. This allows 
        for data and groupby to be passed in or to use previously set values.

        For the sake of efficiency calling this function will not re-apply the 
        groupby operation unless the data, function or the columns are changed. 

        '''
        # store any incoming values
        if isinstance(data, pd.DataFrame):
            self.set_data(data)

        if groupby_cols is not None:
            self.set_groupby_cols(groupby_cols)

        if apply_funct is not None:
            self.set_apply_funct(apply_funct)

        if agg_args is not None:
            self.set_agg_args(agg_args)

        # Do some basic error checks for the most severe problems.
        if not isinstance(self.data, pd.DataFrame):

            msg = "No data set to perform groupby operation"
            raise ValueError(msg)

        if not self.groupby_cols_valid():

            msg = "Columns {} specified for groupby do not exist in data"
            msg = msg.format(self.invalid_cols)
            raise ValueError(msg)

        if self.groupby_cols is None:
            # we have nothing to do. An apply function could be called on the DF
            # but that's not the intent here. Just set result_data=data.
            self.result_data = self.data
        else:
            self.grouped_data = self.data.groupby(self.groupby_cols)

            if not isinstance(self.result_data, pd.DataFrame):
                if self.apply_funct is not None:

                    self.result_data = self.grouped_data.apply(self.apply_funct)

                elif self.agg_args is not None:

                    self.result_data = self.grouped_data.agg(self.agg_args)

        return self.result_data


class MetOfficeFileReader(PandasFileReader):
    '''
    Further specialisation of the PandasFileReader that performs a small amount
    of pre and post-processing in order to prepare the met office data.
    '''
    headers = ["year", "month", "tmax_degc", "tmin_degc", "af_days",
               "rain_mm", "sun_hours"]

    def read(self):
        '''
        Reimplemented read routine, performs pre and post-processing and sets
        self.data equal to the result.
        '''

        skip_n_rows = self.find_first_valid_data()

        df = pd.read_csv(self.file_path, names=self.headers,
                         skiprows=skip_n_rows, *self.args, **self.kwargs)

        # I know that there are some non numeric characters appended to the
        # sun_hours column, lets manually filter these out explicitly.
        df["sun_hours"] = df["sun_hours"].str.replace('#', '')
        df["sun_hours"] = df["sun_hours"].str.replace('*', '')

        # this data set has some odd values in it for missing data, lets force
        # them to be replaced with NaN
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], "coerce")

        # lets reindex with date time, that seems sensible.
        # add a day column - we will pretend it's the 1st of the month
        df["day"] = 1
        date_cols = ["year", "month", "day"]
        df["date_time"] = df[date_cols].apply(lambda s: datetime(*s), axis=1)

        # let's add an average temperature column, not stricly accurate, but
        # will make for a prettier graph.
        df["tavg_degc"] = df['tmax_degc'] + df['tmin_degc']
        df['tavg_degc'] /= 2

        self.data = df.set_index("date_time")

        return None

    def find_first_valid_data(self):
        '''
        Method to find how many rows need to be skipped before the valid data
        starts.

        This method would be very slow if it were required to parse any large
        amount of data, but since it's just to skip 10's of lines it's not
        worth implementing anything more complicated.
        '''
        line_no = 0
        with open(self.file_path) as fh:
            for line in fh:
                # split on any white space
                line_values = line.split(None)

                if not all_numeric(line_values):
                    line_no += 1
                else:
                    break

        return line_no


def calc_min_avg_max_temp(df):

    df = df.agg()

    return df

if __name__ == "__main__":

    url = "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/heathrowdata.txt"
    fp = "~/heathrowdata.txt"

    file_reader = MetOfficeFileReader(fp, sep='\s+')
    raw_df = file_reader.get_dataframe()

    met_temp_grouper = DataGrouper(raw_df)

    agg_dict = {'tmin_degc': 'min', 'tavg_degc': 'mean', 'tmax_degc': 'max'}
    groupby_cols = ['month']
    df = met_temp_grouper(groupby_cols=groupby_cols, agg_args=agg_dict)

    print(df.head())

    plt.plot(df)
    plt.legend(df.columns)
    plt.show()

