from matplotlib import pyplot as plt
import os 


import numpy as np 
import pandas as pd 
import mplfinance as mpf

from market_stats.data import Data
from market_stats.utils import setup_logger

class Plotter:
    def __init__(self,df):
        self.df=df
        self.this_path = os.path.dirname(os.path.abspath(__file__)) 
        self.plots_path = os.path.join(self.this_path, 'plots')
        self.logger= setup_logger('plotter',fp=os.path.join(self.this_path,'logs') )
        self.logger.info('plotter object created')


        
    def simplest_scatter_plot(self,data : Data
                              ,xcol='datetime'
                              ,ycol='close'
                              ,ema_cols=None
                              ,signal_cols=[]
                              ,show=True
                              ,save=True
                              ,subplot=(False, ) # ( True, columnn_name)
                              ,start_date=None # 'start' # yyyy-mm-dd 
                              ,end_date=None#'1995-01-01' # yyyy-mm-dd  'today'
                              ,log_scale=False
                              ,fname='simplest_scatter_plot.png'): 
        if start_date is not None:
            if start_date=='start':
                start_date=self.df['datetime'].min()
            else:
                start_date=pd.to_datetime(start_date)
            self.df=self.df[self.df['datetime']>=start_date]

        if end_date is not None and end_date!='today':
            self.df=self.df[self.df['datetime']<=end_date]
            
        
        plt.scatter(self.df[xcol],self.df[ycol],marker='.',color='black' ) 
        plt.xlabel(xcol)
        plt.ylabel(ycol)
        colors = plt.cm.Blues(np.linspace(0.3, 1, len(ema_cols)))        
        # if ema cols are not none plot them as lines 
        if ema_cols:
            for col, color in zip(ema_cols, colors):
                plt.plot(self.df[xcol], self.df[col], label=col, color=color)
            plt.legend()
            
        if signal_cols:
            for signal_col in signal_cols:
                signal_mask=self.df[signal_col]==1
                plt.scatter(self.df[xcol][signal_mask],self.df[ycol][signal_mask],marker='.', color='green',label=signal_col)
                plt.legend()
        
        if subplot[0]:
            # plot on secondary y axis 
            ax2 = plt.twinx()
            if log_scale:
                ax2.set_yscale('log')
            ax2.plot(self.df[xcol], self.df[subplot[1]], label=subplot[1])
            ax2.legend()

        
        if show:
            plt.show()
        if save:
            plot_fp=os.path.join(self.plots_path,fname)
            plt.savefig(plot_fp)
            



    def candleplot2(self,
                    df,
                    interval,
                    date_column,
                    asset,
                    ser=None,
                    save=True,
                    show=False,
                    **kwargs):

        required_columns = {'open', 'close', 'low', 'high', 'volume'}
        if not required_columns.issubset(df.columns.str.lower()):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

        # Ensure the DataFrame index is a DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.set_index(pd.to_datetime(df[date_column]), inplace=True)

        # Optional: Set the style of the plot
        style = mpf.make_mpf_style(
            base_mpf_style='yahoo',
            rc={'font.size': 10}
        )

        addplots = []
        if ser is not None:
            addplot = mpf.make_addplot(ser, panel=1, color='r', label=kwargs.get('ser_label') or '')
            addplots.append(addplot)

        mindate = df[date_column].iloc[0]
        maxdate = df[date_column].iloc[-1]

        # Capture figure and axes without displaying the plot
        fig, axlist = mpf.plot(
            df,
            type='candle',
            style=style,
            volume=True,
            addplot=addplots,
            title=f'{asset} {interval} \n{mindate} \n{maxdate} \n {str(len(df))} ',
            ylabel='Price',
            ylabel_lower='Volume',
            figsize=(12, 8),
            tight_layout=True,
            returnfig=True  # This prevents automatic display
        )

        plot_fp = None
        if save:
            mindate_str=mindate
            maxdate_str=maxdate
            plot_fp = os.path.join(self.plots_path, f'{asset}_{mindate_str}_{maxdate_str}_{interval}.png')
            fig.savefig(plot_fp)  # Save the figure explicitly
        
        if show:
            plt.show()  # Display only if `show=True`

        plt.close(fig)  # Close figure to prevent display in some environments
        return plot_fp


# Example usage
# Example usage
if __name__ == "__main__":
    # Sample data
    df=pd.read_csv('./market_stats/data/BTC_2020-01-01_2025-01-01.csv')
    df['random']=np.random.randint(0,100,len(df))
    print(df)
    p=Plotter(df)
    p.candleplot2(interval='1d',asset='BTC',df=df,ser=df['random'],date_column='datetime',save=True,show=False)