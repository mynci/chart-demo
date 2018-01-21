# -*- coding: utf-8 -*-
from matplotlib import pyplot as plt

from lib.met_office_tools import MetOfficeFileReader
from lib.groupby import DataGrouper

'''
This uses the MetOfficeFileReader and Generic DataGrouper to prepare data
to be displayed in the static matplotlib chart.

Data source:
https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/heathrowdata.txt

Expected default location of file:
~/heathrowdata.txt

This visalisation shows the minimum, maximum and an average (calculated from a
straight average of the min and max) monthly temperatures across all years of
recorded data at the (by default) Heathrow weather station.

This is purely intended to show that the same data processing toolset can be
used to drive a different output. I have not spent any time on making this
chart look good.
'''


if __name__ == "__main__":

    fp = "~/heathrowdata.txt"

    # Parse the file and get the DataFrame
    file_reader = MetOfficeFileReader(fp, sep='\s+')
    raw_df = file_reader.get_dataframe()

    # Show the first few lines of data
    print(raw_df.head())

    # Build a grouper object
    met_temp_grouper = DataGrouper(raw_df)

    # Configure the grouping and aggregation
    agg_dict = {'tmin_degc': 'min', 'tavg_degc': 'mean', 'tmax_degc': 'max'}
    groupby_cols = ['month']

    # Apply the grouping and aggreagation
    df = met_temp_grouper(groupby_cols=groupby_cols, agg_args=agg_dict)

    # Show the first few lines of the modified data
    print(df.head())

    # Produce a very quick plot of the data
    plt.plot(df)
    plt.legend(df.columns)
    plt.show()

