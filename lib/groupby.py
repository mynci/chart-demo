# -*- coding: utf-8 -*-

'''
Generic data grouping object - this uses the Pandas groupby method and so
expects a Pandas DataFrame on which to work.
'''

import pandas as pd
from .base import SimpleLoggingObject


class DataGrouper(SimpleLoggingObject):
    '''
    Data grouping object.

    This is effectively just a wrapper and chache that sits around the
    Pandas DataFrame groupby-apply framework.

    This object has various get and set methods and can be configured on
    initialisation, on call, using the get/set methods or some combination
    of all three.

    The object should do as little work as necessary to return the result -
    for example chachign the result if nothing has changed.
    '''

    def __init__(self, data=None, groupby_cols=None, apply_funct=None):
        '''
        IInitialise the attributes and store the arguments
        '''
        self.data = data
        self.groupby_cols = groupby_cols
        self.apply_funct = apply_funct
        self.grouped_data = None
        self.result_data = None
        self.invalid_cols = None
        self.agg_args = None
        return None

    def set_groupby_cols(self, columns):
        '''
        Handles a change of the columns that should be grouped on.
        If the columns change then the data is cleaered down to ensure its 
        recalculated.
        '''
        if self.groupby_cols != columns:
            self.groupby_cols = columns
            self.grouped_data = None
            self.result_data = None

        return None

    def set_data(self, data):
        '''
        Handles a change of the input data.If the data change then the outputs 
        are cleared down to ensure its recalculated.
        '''
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

        '''
        Handles a change of the function that could be applied to the groupby
        object. If the function changes then the data is cleaered down to 
        ensure its recalculated.
        '''
        if self.apply_funct != apply_funct:
            self.apply_funct = apply_funct
            self.result_data = None

            if self.agg_args is not None:
                msg = ("Apply function set, updated an aggregation arguments "
                       "were already set, removing the aggregation arguments")
                self.warn(msg)
                self.agg_args = None

        return None

    def set_agg_args(self, agg_args):
        '''
        Handles a change of the arguments that would be passed to
        pandas.groupby.agg(). If the function changes then the data is cleaered
        down to ensure its recalculated.
        '''
        if self.agg_args != agg_args:
            self.agg_args = agg_args
            self.result_data = None

            if self.apply_funct is not None:
                msg = ("Aggregation arguments updated, but an apply function "
                       "was already set, removing the apply function")
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
        for data and configuration to be passed in or to use previously set
        values.

        For the sake of efficiency calling this function will not re-apply the
        groupby operation unless the data or config are changed.

        '''
        # Store any incoming values
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
            # We have nothing to do. An apply function could be called on the DF
            # but that's not the intent here. Just set result_data=data.
            self.result_data = self.data
        else:
            self.grouped_data = self.data.groupby(self.groupby_cols)

            if not isinstance(self.result_data, pd.DataFrame):
                # We need to do something to the grouped data
                if self.apply_funct is not None:
                    # Call apply on the groupby
                    self.result_data = self.grouped_data.apply(self.apply_funct)

                elif self.agg_args is not None:
                    # Call agg on the groupby
                    self.result_data = self.grouped_data.agg(self.agg_args)
                else:
                    # If we get here then we can't do a lot to the data.
                    # raise an error
                    msg = ("No aggregation config or apply function "
                           "specified - cannot continue.")
                    raise ValueError(msg)

        return self.result_data
