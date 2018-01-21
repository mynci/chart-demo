# chart-demo
Code example written by Stephen Kemp.

This code was written from scratch just for the sake of demonstrating coding
style rather than a finished product - a lot more can and would be done to 
fully generalise and extend the code.

I have not put any formal docstring comments in as they are dependant on the
documentation system that might be used. Therefore I have just put a simple
explanation of what all but the most trivial methods do.

It has all been built to display the data from
https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/heathrowdata.txt

Which by default is expected to be found in:
~/heathrowdata.txt

This is a simple demonstrator that can:
- Read an input data file into a pandas dataframe
- Perform some grouping and pre/post-processing on the data set
- Display a static graph of the grouped and filtered data in matplotlib
- Display an interactive graph of the grouped and filtered data in pyqtgraph (Qt5)

To execute the code run one of:
mpl_example.py (simplistic matplotlib example) 
or 
pyqtgrah_example.py (simple interactive chart) 

I realise that everything the data processing side of this tool can do could 
be produced much more quickly, with very little code. However, the intent was to 
demonstrate how a more generic framework could be created that could process
different file types, or data from different files or URLs etc. 

This has been written and tested using XUbuntu 16.04 and Python 3.5.

It requires the following libraries:

pyqt5
pyqtgraph
pandas
matplotlib
numpy

All availible via pip, eg:
sudo pip install pyqt5 pyqtgraph pandas matplotlib numpy
