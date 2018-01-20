# -*- coding: utf-8 -*-

'''
Generic data grouping object
'''

import pandas as pd
from .base import SimpleLoggingObject


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
            # we need to protect this wpdith a type check as dataframes are
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