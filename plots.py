# Step 1: Install mplfinance
# Run this command in your terminal or command prompt
# pip install mplfinance

# Step 2: Import necessary libraries
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

import numpy as np 

from calcview import * 
from utils import setup_logger


# setup logging
plot_logger=setup_logger(name='plot_logger')


def make_my_plot(
    ticker = 'AAPL'
    ,plotname = None 
    ,datefrom = '2020-01-01' 
    ,emas={'name':'CUMDIST_EMA', 'spans': [10,50,100],'secondary_y':True}
    ,indicators=['RSI']
    ):
    colors=['red', 'blue','green','black','yellow','magenta','orange']
    plot_logger.info('making a plot')
    
    if plotname is None:
        plotname=ticker+'_plot'

    c=calcview(ticker)                                    # spawn cv 
    df=c.get_cv(datefrom=datefrom)                        # get data 
    
    # check if indicators column is present in CV 
    for ind in indicators:
        if ind not in df.columns:
            plot_logger.error(f'indicator {indicators} not present in cv columns')
            return None 
    
    # check if ema columns are present in CV 


    # rename columns for plot lib 
    df.rename(columns={
        'OPEN': 'Open',
        'HIGH': 'High',
        'LOW': 'Low',
        'CLOSE': 'Close',
        'VOLUME': 'Volume'
    }, inplace=True)


    # Step 4: Ensure the DataFrame has the required columns and set 'Date' as the index
    df['Date'] = pd.to_datetime(df['TS'])
    df.set_index('Date', inplace=True)

    # Step 6: Create addplots for the indicatorss
    sma_plots=[]
    ema_patches=[]
    no=0
    for no,ema in enumerate(emas['spans']):
        colname=f'{emas["name"]}_{ema}'
        print(colname)
        if no > len(colors)-1:
            plot_logger.error('ran out of colors ')
            return None 
        sma_plot = mpf.make_addplot(df[f'{colname}'], panel=0, color=colors[no], secondary_y=emas['secondary_y'] ,ylabel=f'{colname}')
        sma_plots.append(sma_plot)
        
        patch = mpatches.Patch(color=colors[no], label=f'{colname}')
        ema_patches.append(patch)
    
    for no,ind in enumerate(indicators):
        indicators_plot = mpf.make_addplot(df[ind], panel=2, color=colors[no], secondary_y=False,ylabel=ind)
        sma_plots.append(indicators_plot)
    # Step 7: Use mplfinance.plot to create and display the candlestick plot with subplots
    #mpf.plot(df, type='candle', volume=True, style='yahoo', addplot=[sma_plot, indicators_plot])

    # Step 7: Use mplfinance.plot to create and display the candlestick plot with subplots
    fig,axes=mpf.plot(df, type='candle', volume=True, style='yahoo', addplot=sma_plots, figscale=1.2, title=f'{ticker} Stock Price with indicatorss',returnfig=True)


    # Add legends manually
    # Create custom legend handles

        
    indicators_patch = mpatches.Patch(color='red', label=indicators)

    # Add legend to the main plot (axes[0])
    axes[0].legend(handles=ema_patches, loc='lower left')

# Add legend to the indicators plot (axes[2])
#axes[2].legend(handles=[indicators_patch])
    # savefig 
    plt.savefig(f'./plots/{plotname}.png')

    return fig,axes


def make_my_histogram(data,value,percentile,metric,bins=100,N=3):
    
    # plots histogram with shown value 
    fig,ax=plt.subplots()
    ax.hist(data, bins=bins, edgecolor='black')
    ax.set_xlabel('Value')
    ax.set_ylabel('Frequency')
    ax.set_title(f'Histogram of {metric} = {np.round(value,4)}')
    ax.axvline(value, color='red', linestyle='dashed', linewidth=1)
    loc=(ax.get_ylim()[0] + ax.get_ylim()[1]) / 2
    ax.text(np.round(value,N), loc, f'{np.round(percentile,N)}th percentile', 
        rotation=45, verticalalignment='center', horizontalalignment='center')
    # save fig 
    plt.savefig(f'./plots/histogram.png')
    return f'./plots/histogram.png'

if __name__=='__main__':
    make_my_plot()