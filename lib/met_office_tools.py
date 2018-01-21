# -*- coding: utf-8 -*-
from datetime import datetime
import pandas as pd

from .file_reader import PandasFileReader

'''
Met office specific file reader. This is a specialised version of
PandasFileReader.
'''


def is_numeric(test_str):
    '''
    Simpistic, if not especially fast detection of string that could be
    converted to a numeric type
    '''
    result = True
    if not isinstance(test_str, str):
        msg = "Test value must be a string, not \"{}\"".format(test_str)
        raise TypeError(msg)
    try:
        float(test_str)
    except ValueError:

        result = False

    return result


def all_numeric(val_list):
    '''
    Quick but not optimised detection of whether all values in an iterable type
    are convertable to numeric values.
    '''
    result = all([is_numeric(x) for x in val_list])

    return result


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
        if self.file_path is None:
            return False

        # Find out where the data starts and then let Pandas read the file.
        skip_n_rows = self.find_first_valid_data()

        df = pd.read_csv(self.file_path, names=self.headers,
                         skiprows=skip_n_rows, *self.args, **self.kwargs)

        # I know that there are some non numeric characters appended to the
        # sun_hours column, lets manually remove these explicitly.
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

        return True

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



