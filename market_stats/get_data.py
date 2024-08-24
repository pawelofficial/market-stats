
import pandas as pd 
from datetime import datetime,timedelta
import yfinance as yf
from .utils import setup_logger,exception_logger
import functools
import logging 
from .db import Database
import re 
from  pytickersymbols import PyTickerSymbols
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
    def read_tickers(self):
        df = pd.read_csv('./tmp/nasdaq_screener.csv')
        # Make a dictionary from Symbol and Name columns
        tickers_dict = {'symbol': df['Symbol'].tolist(), 'name': df['Name'].tolist()}
        # Ensure all elements are strings and replace non-alphanumeric characters with underscores
        tickers_dict['symbol_norm'] = [re.sub(r'\W+', '_', str(x)) for x in tickers_dict['symbol']]
        return tickers_dict

    def get_nasdaq_symbols(self):
        #query='select "symbol" from "dev"."nasdaq"'
        #df=self.db.execute_select(query)["symbol"].tolist()
        stock_data = PyTickerSymbols()
        nasdaq_tickers = stock_data.get_stocks_by_index('NASDAQ 100')  # Corrected index name
        stocks=[stock['symbol'] for stock in nasdaq_tickers]
        return stocks 
    
    def get_raw_tables(self):
        query="""
                SELECT table_name, "symbol",s.n_live_tup AS row_count
            FROM "market_stats_raw"."nasdaq"  
            left join information_schema.tables t  
                on table_name = "symbol"
                and  table_schema = 'market_stats_raw'
            LEFT JOIN  pg_stat_user_tables s 
    	    	ON t.table_name = s.relname
    	    	and t.table_schema=s.schemaname
              AND table_type = 'BASE TABLE'
              and table_name !='tmp'
              and table_name!='nasdaq'
              and s.n_live_tup = (select max(n_live_tup) from pg_stat_user_tables where schemaname='market_stats_raw')
              where 1=1 
			    and table_name is not Null
              order by table_name
              ;
        """
        df=self.db.execute_select(query)
        return df['table_name'].tolist()

    def download_many(self,tickers_dict
                      ,start_ts='2020-01-01'
                      ,end_ts='today'
                      ,interval='1d'):

        for no,s in enumerate(tickers_dict['symbol']):
            snorm=tickers_dict['symbol_norm'][no]
            self.db.create_or_replace_ticker_table(snorm)
            self.download_historical_data(tgt_table=s,ticker=s,start_ts=start_ts,end_ts=end_ts,interval=interval)


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
                                 ,schema='market_stats_raw'                  
                                 ):


        # if latest - get latest entry from pg 
        if schema is not None:
            schema=f'"{schema}".'
        else:
            schema=''
        tgt_table=f'"{tgt_table}"'
            
        if start_ts=='latest':
            start_ts=self.db.execute_select(f'select max(ts) ts from {ticker} ')
            if start_ts is not None:
                start_ts=start_ts['ts'].iloc[0]
        # if today - use today 
        if end_ts=='today':
            end_ts= pd.to_datetime(pd.to_datetime(pd.Timestamp.now().normalize()))
            

        start_ts = pd.to_datetime(start_ts) if start_ts is not None else None
        end_ts = pd.to_datetime(end_ts) if end_ts is not None else None
        
        if start_ts is None or end_ts is None:
            raise('ts cant be none ')

               
        df=self.get_data(ticker,start_ts,end_ts,interval)
        # if df is empty log it with warning
        if df.empty:
            self.logger.warning(f"no data for {ticker} from {start_ts} to {end_ts}")
            return None 
        
        
        # if df shape is tiny log it with warning 
        if len(df)<100:
            self.logger.warning(f"df shape is {df.shape}")
        

        # write to tmp table
        df.columns=[col.lower() for col in df.columns]
        self.db.write_tmp_df(df,tmp_table)
        
        
        # merge tmp_table with ticker table on pk 
        query = f"""
            INSERT INTO {schema}{tgt_table } ({', '.join([f'"{col}"' for col in df.columns])})
            SELECT {', '.join([f'src."{col}"' for col in df.columns])} FROM {tmp_table} as src
            ON CONFLICT ({', '.join(pk)})
            DO UPDATE SET
            {', '.join([f'"{col}" = EXCLUDED."{col}"' for col in df.columns])}
        """
        self.logger.info(f"query: {query}")
        self.db.execute_dml(query)
        self.logger.info(f'Historical data for {tgt_table} downloaded and merged with existing data')
              
        

    
    
if __name__=='__main__':


    d=data()
    d.db.connect()
    dic=d.read_tickers()
    symbols=dic['symbol']
    stock_data = PyTickerSymbols()
    nasdaq_tickers = stock_data.get_stocks_by_index('NASDAQ 100')  # Corrected index name

    for no,s in enumerate(symbols):
        snorm=dic['symbol_norm'][no]
        print(s,snorm)
        d.db.create_or_replace_ticker_table(snorm)
        d.download_historical_data(tgt_table=s,ticker=s,start_ts='2020-01-01',end_ts='today',interval='1d')


    exit(1)    
    d.db.connect()

    d.download_historical_data(tgt_table='AAPL',ticker='AAPL',start_ts='2024-01-01',end_ts='today',interval='1d')
    exit(1)
    # recreate objects 
    d.db.execute_dml('drop schema market_stats cascade')
    d.db.execute_dml('create schema market_stats')
    #_=d.db.read_queries()
    #d.db.execure_queries(_)
    
    d.db.create_or_replace_ticker_table('AAPL')
    d.db.create_or_replace_ticker_table('SPX')
    d.download_historical_data(tgt_table='AAPL',ticker='AAPL',start_ts='2020-01-01',end_ts='2024-06-09',interval='1d')
    d.download_historical_data(tgt_table='SPX',ticker='SPX',start_ts='2020-01-01',end_ts='2024-06-09',interval='1d')