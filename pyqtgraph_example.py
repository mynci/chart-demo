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

"""


class DataProcessorThread(QtCore.QObject):

    sig_new_data = pg.QtCore.pyqtSignal(pd.DataFrame)
    sig_update_hist_data = pg.QtCore.pyqtSignal(dict, int, dict)

    def __init__(self, file_path=None, *args, **kwargs):

        super(DataProcessorThread, self).__init__(*args, **kwargs)
        self.met_file_reader = None
        self.met_temp_grouper = None
        self.update_file_path(file_path)

        return None

    @pg.QtCore.pyqtSlot(str)
    def update_file_path(self, file_path):
        if self.met_file_reader is None:
            self.met_file_reader = MetOfficeFileReader(file_path, sep="\s+")
        else:
            self.met_file_reader.set_file_path(file_path)

        if file_path is not None:
            self.process_data()

        return None

    @pg.QtCore.pyqtSlot()
    def process_data(self):

        raw_df = self.met_file_reader.get_dataframe()

        if self.met_temp_grouper is None:
            met_temp_grouper = DataGrouper(raw_df)
        else:
            met_temp_grouper.set_data(raw_df)

        agg_dict = {"tmin_degc": "min", "tavg_degc": "mean",
                    "tmax_degc": "max"}
        groupby_cols = ["month"]

        df = met_temp_grouper(groupby_cols=groupby_cols, agg_args=agg_dict)
        self.sig_new_data.emit(df)

        return None

    @pg.QtCore.pyqtSlot(float)
    def filter_month(self, month_no):

        df = self.met_file_reader.get_dataframe()

        month_no = round(month_no, 0)
        month_no = max(month_no, df["month"].min())
        month_no = min(month_no, df["month"].max())
        month_nos = df[df["month"] >= month_no]["month"]

        if month_nos.shape[0] > 1:
            month_no = month_nos.min()
        else:
            month_no = 1

        df = df[df["month"] == month_no]

        cols = ["tmin_degc", "tavg_degc", "tmax_degc"]
        data = {}
        bins = np.arange(-5, 40, 0.5)

        for col in cols:

            density, bins = np.histogram(df[col], bins=bins, normed=True,
                                         density=True)
            density = 100.0 * (density / density.sum())

            data[col] = (-1.0 * bins, density)

        temp_vals = {"tmin_degc": df["tmin_degc"].min(),
                     "tavg_degc": df["tavg_degc"].mean(),
                     "tmax_degc": df["tmax_degc"].max()}

        self.sig_update_hist_data.emit(data, month_no, temp_vals)

        return None


class MainWindow(QtGui.QMainWindow):

    sig_req_new_data = pg.QtCore.pyqtSignal()
    sig_set_file_path = pg.QtCore.pyqtSignal(str)
    sig_req_hist_data = pg.QtCore.pyqtSignal(float)

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.time_series_plots = {}
        self.histogram_plots = {}
        self.month_no = 0

        self.init_gui()
        self.data_processor = DataProcessorThread()
        self.data_thread = QtCore.QThread()
        self.data_processor.moveToThread(self.data_thread)

        self.data_thread.start()
        self.sig_set_file_path.connect(self.data_processor.update_file_path)
        self.sig_req_new_data.connect(self.data_processor.process_data)

        self.data_processor.sig_new_data.connect(self.update_time_series_charts)

        self.sig_req_hist_data.connect(self.data_processor.filter_month)
        self.data_processor.sig_update_hist_data.connect(self.update_histogram_chart)

        self.showMaximized()
        self.txt_file_path.setText("~/heathrowdata.txt")
        self.sig_req_hist_data.emit(1)
        return None

    def init_gui(self):
        """
        General GUI setup, if it was much more complex we might want to use a 
        ui file built in QT Creator.
        """

        # create a vbox to hold the text box and both charts
        vbox = QtGui.QVBoxLayout()

        # the hbox will keep the charts side by side.
        hbox = QtGui.QHBoxLayout()

        self.txt_file_path = pg.QtGui.QLineEdit()
        self.txt_file_path.textChanged[str].connect(self.set_file_path)

        self.time_series_widget = pg.PlotWidget()
        self.time_series_plt_item = self.time_series_widget.getPlotItem()
        title_text = ("Time Series Monthly Temperature "
                      "data (1948 - 2017) (degC)")
        self.time_series_plt_item.setTitle(title_text)
        ax = self.time_series_plt_item.getAxis("bottom")
        ax.setTicks([[[i, calendar.month_name[i]] for i in range(1, 13)]])
        self.time_series_plt_item.addLegend()

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

        self.histogram_widget = pg.PlotWidget()
        self.hist_plt_item = self.histogram_widget.getPlotItem()

        self.hist_plt_item.setYLink(self.time_series_plt_item)
        self.roi = pg.InfiniteLine(pos=(1), movable=True, pen=(147, 112, 219),
                                   hoverPen=(204, 204, 0))

        self.roi.sigPositionChanged.connect(self.roi_moved)
        self.hist_plt_item.addLegend()

        self.time_series_widget.addItem(self.roi)
        vbox.addWidget(self.txt_file_path)
        hbox.addWidget(self.time_series_widget)
        hbox.addWidget(self.histogram_widget)

        vbox.addLayout(hbox)

        self.central_widget = QtGui.QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(vbox)

        return None

    @pg.QtCore.pyqtSlot(str)
    def set_file_path(self, file_path):
        file_path = os.path.expanduser(file_path)
        if os.path.isfile(file_path):
            self.sig_set_file_path.emit(file_path)

        return None

    @pg.QtCore.pyqtSlot(pd.DataFrame)
    def update_time_series_charts(self, df):

        for col in df.columns:

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

            plot = self.time_series_plots[col]

            plot.setData(df.index, df[col].values)

        return None

    @pg.QtCore.pyqtSlot(dict, int, dict)
    def update_histogram_chart(self, data, month_no, temp_values):

        if self.month_no != month_no:

            self.month_no = month_no

            for col, series_data in data.items():

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

                    color.setAlphaF(0.7)
                    plot = self.hist_plt_item.plot(stepMode=True,
                                                   fillLevel=0,
                                                   pen=None,
                                                   brush=color,
                                                   name=label)
                    plot.setZValue(zorder)
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

            month_name = calendar.month_name[month_no]
            title_text = "Histogram data for {} (1948 - 2017)".format(month_name)
            self.hist_plt_item.setTitle(title_text)

        return None

    @pg.QtCore.pyqtSlot(object)
    def roi_moved(self, roi):
        roi_x_pos = roi.pos().x()
        self.sig_req_hist_data.emit(roi_x_pos)
        return None

if __name__ == "__main__":

    url = "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/heathrowdata.txt"
    fp = "~/heathrowdata.txt"

    QtGui.QApplication.setDesktopSettingsAware(False);

    app = QtGui.QApplication([])
    mw = MainWindow()
    mw.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        QtGui.QApplication.instance().exec_()
