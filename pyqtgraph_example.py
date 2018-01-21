# -*- coding: utf-8 -*-
import sys
import os
import calendar

import pandas as pd
import pyqtgraph as pg
import numpy as np
from pyqtgraph import QtGui, QtCore

from lib.met_office_tools import MetOfficeFileReader
from lib.groupby import DataGrouper

"""
This uses the MetOfficeFileReader and Generic DataGrouper to prepare data
to be displayed in the interactive charts.

Data source:
https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/heathrowdata.txt

Expected default location of file:
~/heathrowdata.txt

This visualisation shows the minimum, maximum and an average (calculated from a
straight average of the min and max) monthly temperatures across all years of
recorded data at the (by default) Heathrow weather station.

The histogram gives a breakdown of the raw data that fed created the aggregate
values used in the time series plot for whichever month is selected.

"""


class DataProcessorThread(QtCore.QObject):

    '''
    For this example we don't have enough data to require a seperate thread
    but it's always best to build one otherwise data processing can lock up
    the GUI.

    This object will be moved to another QThread and will interact with the
    GUI via the Qt signal and slots interface.

    This object will take a file path and use the MetOfficeFileReader and
    DataGrouper objects to prepare the data to be visualised.

    This object will also respond to the interactive components to allow the
    user to select a particular month by dragging the purple line.
    '''

    # define the signals that this object can send
    sig_new_data = pg.QtCore.pyqtSignal(pd.DataFrame)
    sig_update_hist_data = pg.QtCore.pyqtSignal(dict, int, dict)
    sig_send_year_lims = pg.QtCore.pyqtSignal(int, int)

    def __init__(self, file_path=None, *args, **kwargs):

        super(DataProcessorThread, self).__init__(*args, **kwargs)
        self.met_file_reader = None
        self.met_temp_grouper = None
        self.update_file_path(file_path)

        return None

    @pg.QtCore.pyqtSlot(str)
    def update_file_path(self, file_path):

        '''
        Use the MetOfficeFileReader to read the data and then call
        process_data() in order to perform the required aggregation.
        '''

        if self.met_file_reader is None:
            self.met_file_reader = MetOfficeFileReader(file_path, sep="\s+")
        else:
            self.met_file_reader.set_file_path(file_path)

        if file_path is not None:
            self.process_data()

        return None

    @pg.QtCore.pyqtSlot()
    def process_data(self):

        '''
        Slot to handle the update of the data source. This will perform any
        grouping and aggregation using the DataGrouper and send the
        time-series data to the GUI for display.

        It additionally sends the min and max year found in the data so that
        the titles in the GUI will reflect the source data.
        '''

        # Get the raw data from the file reader and populate the min/max years.
        raw_df = self.met_file_reader.get_dataframe()

        min_year = raw_df['year'].min()
        max_year = raw_df['year'].max()

        # only inititalise the grouper if required.
        if self.met_temp_grouper is None:
            met_temp_grouper = DataGrouper(raw_df)
        else:
            met_temp_grouper.set_data(raw_df)

        # Setup the way in which we want to aggregate this data within the
        # pandas groupby/agg methodology and perform the operation.
        agg_dict = {"tmin_degc": "min", "tavg_degc": "mean",
                    "tmax_degc": "max"}
        groupby_cols = ["month"]

        df = met_temp_grouper(groupby_cols=groupby_cols, agg_args=agg_dict)

        # Send the data to the GUI.
        self.sig_new_data.emit(df)
        self.sig_send_year_lims.emit(min_year, max_year)
        self.filter_month(1)
        return None

    @pg.QtCore.pyqtSlot(float)
    def filter_month(self, month_no):
        '''
        Slot to handle the interactive update of the histogram data.
        This is sent a float as it's the position of the vertical line, the
        conversion to a valid month is done in the data processing thread to
        keep the GUI as light as possible.
        '''

        # Get the raw data
        df = self.met_file_reader.get_dataframe()

        # Round, apply limits and filter the month data
        month_no = round(month_no, 0)
        month_no = max(month_no, df["month"].min())
        month_no = min(month_no, df["month"].max())
        month_nos = df[df["month"] >= month_no]["month"]

        # Pick the lowest month left in the dataframe, or use 1.
        if month_nos.shape[0] > 1:
            month_no = month_nos.min()
        else:
            month_no = 1

        # filter the required month
        df = df[df["month"] == month_no]

        # Set the columns we want to get the data for, the bins we will fill
        # with the temperature counts and something to store it in
        cols = ["tmin_degc", "tavg_degc", "tmax_degc"]
        data = {}
        bins = np.arange(-5, 40, 0.5)

        for col in cols:
            # Calculate the bins and density information for the current column
            # note we need to dropna just incase we have any bad values - the
            # np.histogram method cannot handle NaN.
            density, bins = np.histogram(df[col].dropna(), bins=bins,
                                         normed=True, density=True)
            # At this stage the areas of the columns would add up to 1
            # for this kind of data it makes more sense for the heights to add
            # up to 100 - effectively a "percentage of time" metric
            density = 100.0 * (density / density.sum())

            # Store the data as an x,y pair.
            data[col] = (-1.0 * bins, density)

        # Calculate the temperature values, used to place the markers
        # on the time series plots.
        temp_vals = {"tmin_degc": df["tmin_degc"].min(),
                     "tavg_degc": df["tavg_degc"].mean(),
                     "tmax_degc": df["tmax_degc"].max()}

        # Send the data to the GUI
        self.sig_update_hist_data.emit(data, month_no, temp_vals)

        return None


class MainWindow(QtGui.QMainWindow):

    '''
    Main GUI window. This should do as little as possible that isn't directly
    GUI related.

    It will display a text box (file path) and two interactive charts.

    The left hand chart shows the min, max and average temperatures for
    all years grouped by month from the input data.

    The right hand chart shows three overlapping histograms of all of the years
    temperatures for the selected month. Slect a different month by dragging
    the purple ROI line on the left hand chart.

    '''
    # Setup the signals
    sig_req_new_data = pg.QtCore.pyqtSignal()
    sig_set_file_path = pg.QtCore.pyqtSignal(str)
    sig_req_hist_data = pg.QtCore.pyqtSignal(float)

    def __init__(self, *args, **kwargs):

        # Basic initialisation
        super(MainWindow, self).__init__(*args, **kwargs)

        self.time_series_plots = {}
        self.histogram_plots = {}
        self.month_no = 0
        self.min_year = None
        self.max_year = None

        # Initialise the GUI aspects
        self.init_gui()

        # Create a data processing object in a seperate thread
        self.data_processor = DataProcessorThread()
        self.data_thread = QtCore.QThread()
        self.data_processor.moveToThread(self.data_thread)
        self.data_thread.start()

        self.connect_signals()

        self.showMaximized()

        # hard code a default path, just for the sake of making testing easier.
        self.txt_file_path.setText("~/heathrowdata.txt")
        return None

    def init_gui(self):
        """
        General GUI setup, if it was more complex we might want to use a
        ui file built in Qt Creator.
        """

        # Create a vbox to hold the text box and both charts
        vbox = QtGui.QVBoxLayout()

        # The hbox will keep the charts side by side.
        hbox = QtGui.QHBoxLayout()

        # Create a text box and connect the changed signal to a slot
        # it would be trivial to add a 'browse' dialog, but not required for
        # a demo
        self.txt_file_path = pg.QtGui.QLineEdit()
        self.txt_file_path.textChanged[str].connect(self.set_file_path)

        # Chart specific setup
        self.setup_time_series_charts()
        self.setup_histogram_chart()

        # Build up the GUI
        vbox.addWidget(self.txt_file_path)
        hbox.addWidget(self.time_series_widget)
        hbox.addWidget(self.histogram_widget)

        vbox.addLayout(hbox)

        self.central_widget = QtGui.QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(vbox)

        return None

    def connect_signals(self):
        '''
        Connect the signals from the GUI to the data processor and vice-versa
        again.
        '''
        self.sig_set_file_path.connect(self.data_processor.update_file_path)
        self.sig_req_new_data.connect(self.data_processor.process_data)

        self.data_processor.sig_new_data.connect(self.update_time_series_charts)

        self.sig_req_hist_data.connect(self.data_processor.filter_month)
        self.data_processor.sig_update_hist_data.connect(self.update_histogram_chart)
        self.data_processor.sig_send_year_lims.connect(self.set_min_max_year)

        return None

    def setup_time_series_charts(self):
        '''
        Configure the time series plots.

        This is in a seperate method just for the sake of organisation.
        '''
        self.time_series_widget = pg.PlotWidget()
        self.time_series_plt_item = self.time_series_widget.getPlotItem()

        # Modify the x axis to show the month names
        ax = self.time_series_plt_item.getAxis("bottom")
        ax.setTicks([[[i, calendar.month_name[i]] for i in range(1, 13)]])

        # Add a legend - this can be moved by the user
        self.time_series_plt_item.addLegend()

        # Setup the markers to highlight the selected month
        self.min_marker = self.time_series_plt_item.plot(symbolPen='b',
                                                         symbolBrush='w',
                                                         symbol='o',
                                                         symbolSize=10,
                                                         pxMode=True)

        self.mean_marker = self.time_series_plt_item.plot(symbolPen='g',
                                                          symbolBrush='w',
                                                          symbol='o',
                                                          symbolSize=10,
                                                          pxMode=True)

        self.max_marker = self.time_series_plt_item.plot(symbolPen='r',
                                                         symbolBrush='w',
                                                         symbol='o',
                                                         symbolSize=10,
                                                         pxMode=True)

        # Add the dragable line
        self.roi = pg.InfiniteLine(pos=(1), movable=True, pen=(147, 112, 219),
                                   hoverPen=(204, 204, 0))

        # connect the signal for line moved to a slot
        self.roi.sigPositionChanged.connect(self.roi_moved)

        # Add the ROI to the timer-series chart
        self.time_series_widget.addItem(self.roi)

        return None

    def setup_histogram_chart(self):
        '''
        Configure the histogram plots.

        This is in a seperate method just for the sake of organisation.
        '''
        self.histogram_widget = pg.PlotWidget()
        self.hist_plt_item = self.histogram_widget.getPlotItem()

        # Link the Y axis of the two plots - we want the scale to stay the same
        self.hist_plt_item.setYLink(self.time_series_plt_item)

        # Add a legend. Horrible to hard code the position and should have a
        # placement algorithm defined at some stage. User can move it if
        # covering the data.
        self.hist_plt_item.addLegend(offset=(550, 800))
        return None

    @pg.QtCore.pyqtSlot(str)
    def set_file_path(self, file_path):
        '''
        Slot to handle the text changing in the text box.
        It will only be passed to the data processor if it's a valid path.
        If this were a slower operation (perhaps if it were reading a URL or
        similar then it may be better to allow the data processor to handle the
        test.
        '''
        file_path = os.path.expanduser(file_path)
        if os.path.isfile(file_path):
            # Before we send a new path, clear down the current month
            # This will ensure that new data causes an update of the histograms
            self.month_no = None
            self.sig_set_file_path.emit(file_path)

        return None

    @pg.QtCore.pyqtSlot(int, int)
    def set_min_max_year(self, min_year, max_year):
        '''
        Slot to update the minimum and maximum years and update the chart title
        '''
        self.min_year = min_year
        self.max_year = max_year

        title_text = ("Time Series Monthly Temperature "
                      "data ({} - {}) (degC)".format(self.min_year,
                                                     self.max_year))

        self.time_series_plt_item.setTitle(title_text)

        return None

    @pg.QtCore.pyqtSlot(pd.DataFrame)
    def update_time_series_charts(self, df):
        '''
        Slot to handle new time series data. This is only likely to be called
        once per file opened.
        '''

        for col in df.columns:
            # If this is the first time, create the charts.
            if col not in self.histogram_plots:
                if "min" in col:
                    pen = pg.QtGui.QPen(pg.QtGui.QColor("blue"), 0)
                    label = "Minimum Monthly Temperature (All Years) (degC)"
                elif "max" in col:
                    pen = pg.QtGui.QPen(pg.QtGui.QColor("red"), 0)
                    label = "Maximum Monthly Temperature (All Years) (degC)"
                else:
                    pen = pg.QtGui.QPen(pg.QtGui.QColor("green"), 0)
                    label = "Average Monthly Temperature (All Years) (degC)"

                plot = self.time_series_plt_item.plot(pen=pen, name=label)

                self.time_series_plots[col] = plot

            # Select the correct plot and update the data
            plot = self.time_series_plots[col]

            plot.setData(df.index, df[col].values)

        return None

    @pg.QtCore.pyqtSlot(dict, int, dict)
    def update_histogram_chart(self, data, month_no, temp_values):
        '''
        Slot to handle an update of the data shown in the histogram and the
        highlight datapoints. This would be called whenever the user selected
        a new month using the line on the time series plots.
        '''
        if self.month_no != month_no:
            # only update if something has actually changed
            self.month_no = month_no

            for col, series_data in data.items():
                # Create the plots only if they don't already exist.
                if col not in self.histogram_plots:

                    if "min" in col:
                        color = pg.QtGui.QColor("blue")
                        zorder = 0
                        label = "Minimum Monthly Temperatures (All Years) (degC)"

                    elif "max" in col:
                        color = pg.QtGui.QColor("red")
                        zorder = 0
                        label = "Maximum Monthly Temperatures (All Years) (degC)"

                    else:
                        color = pg.QtGui.QColor("green")
                        zorder = 10
                        label = "Average Monthly Temperatures (All Years) (degC)"

                    # Create a copy of the colour - as the pen should not be
                    # made semi-transparent
                    pen_color = pg.QtGui.QColor(color)
                    color.setAlphaF(0.3)
                    plot = self.hist_plt_item.plot(stepMode=True,
                                                   fillLevel=0,
                                                   pen=pen_color,
                                                   brush=color,
                                                   name=label)
                    plot.setZValue(zorder)
                    # Rotate it as we want the bins (temperature) to match the
                    # time series chart.
                    plot.rotate(-90)
                    self.histogram_plots[col] = plot

                plot = self.histogram_plots[col]

                plot.setData(*series_data)

                if "min" in col:
                    self.min_marker.setData([month_no], [temp_values[col]])

                elif "max" in col:
                    self.max_marker.setData([month_no], [temp_values[col]])

                else:
                    self.mean_marker.setData([month_no], [temp_values[col]])

            # Update the title
            month_name = calendar.month_name[month_no]
            title_text = "Histogram data for {} ({} - {})"
            title_text = title_text.format(month_name, self.min_year,
                                           self.max_year)
            self.hist_plt_item.setTitle(title_text)

        return None

    @pg.QtCore.pyqtSlot(object)
    def roi_moved(self, roi):
        # This clot handles the ROI being moved. It simply extracts the x
        # coordinate in chart coordinate system and passes it to the data
        # processor.
        roi_x_pos = roi.pos().x()
        self.sig_req_hist_data.emit(roi_x_pos)
        return None

if __name__ == "__main__":

    # Boiler plate to run a Qt App.
    app = QtGui.QApplication([])
    mw = MainWindow()
    mw.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        QtGui.QApplication.instance().exec_()
