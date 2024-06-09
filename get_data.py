
import pandas as pd 
from datetime import datetime,timedelta
import yfinance as yf
from utils import setup_logger,exception_logger
import functools
import logging 
from db import Database

# set up log 




@exception_logger
class data:
    def __init__(self):
        
        #self.logger=setup_logger('data',fp='./logs/')
        self.logger.info('Data object created')
        self.tickers_map={
            'SPX':{'yf':'^GSPC','desc':'S&P 500 index ' }
                          }
        self.db=Database()
        self.data_types={
            'ts': lambda x: pd.to_datetime(x, format='%Y-%m-%d %H:%M:%S'),
            'open':lambda x: float(x),
            'high':lambda x: float(x),
            'low':lambda x: float(x),
            'close':lambda x: float(x),
            'volume':lambda x: float(x)
        }

        #self.apply_decorator()
        # download data from yfinance
    def get_data(self
                 ,ticker 
                 ,start_ts=None      # default today start of the day 
                 ,end_ts=None        # default today end of the day 
                 ,interval=None      # default 1m
                 ,timedelta_days=3   # start of the day days ago 
                 ):
        
        start_ts=start_ts = start_ts if start_ts else datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=timedelta_days)
        end_ts=end_ts if end_ts else datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)

        interval=interval if interval else '1m'
        
        if ticker in self.tickers_map.keys():
            ticker_mapped=self.tickers_map[ticker]['yf']
        else:
            ticker_mapped=ticker
        self.logger.info(f'Getting data for {ticker} / {ticker_mapped} from {start_ts} to {end_ts} ({ (end_ts-start_ts).days} days )  with interval {interval}')
        # download df from yfinance 
        
        data = yf.download(ticker_mapped, start=start_ts, end=end_ts + timedelta(days=1), interval=interval)
        data.columns=[col.lower() for col in data.columns]
        data['ticker']=ticker
        data['ts']=data.index
        # format ts from  09:30:00-04:00 to 09:30:00
        data['ts']=data['ts'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
        
        # reset index 
        data.reset_index(drop=True,inplace=True)
        # drop adj close column 
        data.drop('adj close',axis=1,inplace=True)        
        
        # cast column names to lwercast 
        
        
        # cast columns to their data types 
        for col in self.data_types.keys():
            data[col]=data[col].apply(self.data_types[col])
        
        # log metadata 
        self.logger.info(f'{ticker} data shape: {data.shape}')
        return data     
    
    
    # merges data into tgt_table
    def download_historical_data(self
                                 ,tgt_table
                                 ,tmp_table='tmp'
                                 ,ticker='SPX'
                                 ,pk=('ts','ticker') # primary key
                                 ,df = None
                                 ,start_ts = None 
                                 ,end_ts   = None 
                                 ,interval = None                         
                                 ):
        # convert start_ts and end_ts to datetime from strings 
        start_ts = pd.to_datetime(start_ts) if start_ts is not None else None
        end_ts = pd.to_datetime(end_ts) if end_ts is not None else None
        
        
        df=self.get_data(ticker,start_ts,end_ts,interval)

        # write to tmp table
        df.columns=[col.lower() for col in df.columns]
        self.db.write_tmp_df(df,tmp_table)
        # merge tmp_table with ticker table on pk 
        query = f"""
            INSERT INTO {tgt_table} ({', '.join([f'"{col}"' for col in df.columns])})
            SELECT {', '.join([f'src."{col}"' for col in df.columns])} FROM {tmp_table} as src
            ON CONFLICT ({', '.join(pk)})
            DO UPDATE SET
            {', '.join([f'"{col}" = EXCLUDED."{col}"' for col in df.columns])}
        """
        self.db.execute_dml(query)
        self.logger.info(f'Historical data for {tgt_table} downloaded and merged with existing data')
              
        

    
    
if __name__=='__main__':


    d=data()
    d.db.connect()
    # recreate objects 
    d.db.execute_dml('drop schema market_stats cascade')
    d.db.execute_dml('create schema market_stats')
    #_=d.db.read_queries()
    #d.db.execure_queries(_)
    
    d.db.create_or_replace_ticker_table('AAPL')
    d.db.create_or_replace_ticker_table('SPX')
    d.download_historical_data(tgt_table='AAPL',ticker='AAPL',start_ts='2020-01-01',end_ts='2024-06-09',interval='1d')
    #d.download_historical_data(tgt_table='SPX',ticker='SPX')