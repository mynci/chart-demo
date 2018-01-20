# -*- coding: utf-8 -*-
from matplotlib import pyplot as plt

from lib.met_office_tools import MetOfficeFileReader
from lib.groupby import DataGrouper

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


if __name__ == "__main__":

    url = "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/heathrowdata.txt"
    fp = "~/heathrowdata.txt"

    file_reader = MetOfficeFileReader(fp, sep='\s+')
    raw_df = file_reader.get_dataframe()

    print(raw_df.head())
    met_temp_grouper = DataGrouper(raw_df)

    agg_dict = {'tmin_degc': 'min', 'tavg_degc': 'mean', 'tmax_degc': 'max'}
    groupby_cols = ['month']

    df = met_temp_grouper(groupby_cols=groupby_cols, agg_args=agg_dict)

    print(df.head())

    plt.plot(df)
    plt.legend(df.columns)
    plt.show()

