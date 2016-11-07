"""this script prepares ASX short interest data and plots it
with Yahoo Finance data."""

import datetime
import matplotlib.pyplot as plt
import pandas as pd
import pandas.io.data as web

# function to correctly format data from ASX data
def asx_date_fix(x):
    # dd-mm-YYYY to YYYY-mm-dd
    return "%s-%s-%s" % (x[-4:], x[3:5], x[:2])

# function for plotting outputs based on an input datafram "df"
def multi_plot(df, store=False):
    # set symbol value for use in title and output
    symbol = df.sym.values[0]

    fig = plt.figure() # create figure object
    fig.set_figheight(10) # set height of figure
    fig.set_figwidth(15) # set width of figure

    # create first plot in figure of open and close price
    ax1 = fig.add_subplot(411)
    ax1.plot(df.Date, df.Close, label="Close")
    ax1.plot(df.Date, df.Open, label="Open")
    ax1.legend(frameon=False)
    ax1.set_title(symbol)
    ax1.set_ylabel("Price")

    # create second plot of volume traded
    ax2 = fig.add_subplot(412, sharex=ax1)  # x axis is shared
    ax2.plot(df.Date, df.Volume)
    ax2.set_ylabel("Volume Traded")

    ax3 = fig.add_subplot(413, sharex=ax1)
    ax3.plot(df.Date, df.percentageShort)
    ax3.set_ylabel("Percentage Short")

    ax4 = fig.add_subplot(414, sharex=ax1)
    ax4.plot(df.Date, df.vol)
    ax4.set_ylabel("Intraday Volatility")

    # specify whether to store or display plots
    # if saved, save with high resolution: "dpi=600"
    if store:
        fig.savefig("/Users/hharris/%s.png" % symbol, dpi=600)
    else:
        plt.show()


if __name__ == "__main__":

    # import splitted csv files from ASX data (see shell_script.txt for pre-steps)
    directory = '~/Desktop/short/'
    date = pd.read_csv('%sdate.csv' % (directory))
    data = pd.read_csv('%sjoined.csv' % (directory))

    # modify ASX data
    data.rename(columns = {'Unnamed: 0':'company','Unnamed: 1':'symbol'},
            inplace = True)
    company_info = data[['company','symbol']]

    percent_short = data.filter(regex='Total Product in Issue')
    reported_short = data.filter(regex='Reported Short Positions')

    datelist = date.columns.values
    datelist = [x for x in datelist if not x.startswith('Unnamed')]

    percent_short.columns = datelist
    reported_short.columns = datelist

    output_percent = pd.concat([company_info,percent_short], axis=1)
    output_reported_short = pd.concat([company_info,reported_short], axis=1)

    per = output_percent.dropna()
    report = output_reported_short.dropna()

    # reshape the data so that dates to have dates as rows
    per = pd.melt(per, id_vars=["company", "symbol"],
            var_name="date", value_name="percentageShort")

    report = pd.melt(report, id_vars=["company", "symbol"],
            var_name="date", value_name="reportedShort")

    # adjust columns to fit with Yahoo Finance data for merge
    per['sym'] = [x.strip() + '.AX' for x in per['symbol'].values]
    per['Date'] = [asx_date_fix(x) for x in per.date.values]
    report['sym'] = [x.strip() + '.AX' for x in report['symbol'].values]
    report['Date'] = [asx_date_fix(x) for x in report.date.values]

    # Gather Yahoo Finance data using API
    start = datetime.datetime(2016, 1, 4)
    end = datetime.datetime(2016, 10, 28)
    # set a list of securities of interest, this can be adjusted.
    securities = ['WBC.AX', 'CBA.AX', 'ANN.AX', 'COH.AX']

    dickt = {}  # create dictionary for storing API data
    # loop through securities of interest and gather data
    for i in securities:
        f = web.DataReader(i, 'yahoo', start, end)
        f['sym'] = i # populate the 'sym' column
        f['vol'] = 100 * (f.High - f.Low)/ f.Open # populate the 'vol' column
        f = f.reset_index() # remove date index for merge
        f['Date'] = [x.astype(str)[:10] for x in f.Date.values]

        # add in ASX short interest data using a merge
        f = pd.merge(per[per.sym == i], f, how='inner', on=['sym','Date'])
        f = pd.merge(report[report.sym == i], f, how='inner', on=['sym','Date'])
        # set 'Date' column to be in correct format for plotting
        f['Date'] = [datetime.datetime.strptime(x, "%Y-%m-%d") for x in f.Date.values]

        # utilise plot function to produce plots for each security
        multi_plot(f, store=True)
