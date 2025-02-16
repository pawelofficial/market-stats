from .db import *
from .utils import setup_logger,exception_logger

class calcview:
    def __init__(self, ticker):
        self.logger=setup_logger('calcview',fp='./logs/')
        self.logger.info('calcview object created')
        self.ticker=ticker 
        self.db=Database()
        self.db.schema='dev'
        self.src_schema='market_stats_raw'
        self.limit =''
        self.df=None
        self.base_df = None # base df without aggregation or any emas 
        self.agg_lvl = None # aggregation level 
        self.ma_cols=['OPEN','HIGH','LOW','CLOSE']
        self.indicator_columns=['RSI','MACD']
        self.ma_spans=[5,10,20,50,100,200]
        
    def get_base_columns(self):
        base_cols=['ID','TS','OPEN','HIGH','LOW','CLOSE','VOLUME','TICKER']
        query="SELECT column_name FROM information_schema.columns WHERE table_name = 'CV_ALL'"
        cols=self.db.execute_select(query)['column_name'].tolist()
        metric_cols=[c for c in cols if c not in base_cols]
        return base_cols,metric_cols
        
        
    def get_data(self,ticker = None ,limit = None ):
        if self.db.is_connected==False:
            self.db.connect()
        ticker=ticker if ticker is not None  else self.ticker
        limit=f'limit {limit}' if limit is not None else self.limit
        self.df=self.db.execute_select(f'select * from "{self.src_schema}"."{ticker}" {limit} ' )
        # capitalize column names
        self.df.columns=[col.upper() for col in self.df.columns]
        self.base_df=self.df.copy()
        return self.df
    # fetches calcview 
    def get_cv(self,cv_name=None,limit=None,datefrom = '2020-01-01',capitalize=False ): 
        if cv_name is None:
            cv_name=f'"CALC_VIEW_{self.ticker}"'
        if self.db.is_connected==False:
            self.db.connect()
        limit=f'limit {limit}' if limit is not None else self.limit               # limit clause 
        where = '' if datefrom is None else f'where \"TS\"::date > \'{datefrom}\'::date ; '  # where clause 
        query = f'select * from "dev".{cv_name} {where} {limit} '
        df=self.db.execute_select(query )
        # capitalize column names
        if capitalize:
            df.columns=[col.upper() for col in df.columns]
        return df
        
    # aggregate to span in seconds 
    def aggregate(self, interval,inplace=True):
        # Map provided intervals to pandas offset aliases
        interval_map = {
            '1m': 'T',  # 1 minute
            '5m': '5T',  # 5 minutes
            '15m': '15T',  # 15 minutes
            '1h': 'H',  # 1 hour
            '4h': '4H',  # 4 hours
            '1d': 'D',  # 1 day
            '1w': 'W',  # 1 week
            '1M':'M'    # 1  month
        }
        if interval not in interval_map.keys():
            self.logger.error(f'no such interval as {interval}')
            return 
        self.agg_lvl=interval 
        
        # Ensure df is a DataFrame with a DateTimeIndex
        if not isinstance(self.df.index, pd.DatetimeIndex):
            # Assuming there's a column 'datetime' in self.df to set as index
            # Convert it to datetime and set as index
            self.df['TS'] = pd.to_datetime(self.df['TS'])
            self.df.set_index('TS', inplace=True)

        def array_agg(series):
            return list(series)
        # Define custom aggregation logic
        agg_dict = {
            'ID':array_agg
            ,'OPEN': 'first',
            'HIGH': 'max',
            'LOW': 'min',
            'CLOSE': 'last'
        }


        # Check if the interval is in the map, else default to 'D' (1 day)
        pandas_interval = interval_map.get(interval, 'D')
        # Resample and aggregate
        aggregated_df = self.df.resample(pandas_interval).agg(agg_dict)
        # Handle missing data (optional, based on your requirement)
        # For example, forward fill missing data
        aggregated_df.ffill(inplace=True)
        aggregated_df['agg_lvl']=interval

        # mutate self. df 
        if inplace:
            self.df=aggregated_df.copy()
            
        return aggregated_df
            
        
    # calculates EMA ans SMA on MA_cols with ma_spans
    def calculate_mas(self,cols=None,spans=None):
        cols=cols if cols is not None else self.ma_cols
        spans=spans if spans is not None else self.ma_spans
        for c in cols:
            for s in spans:
                self.df[f'SMA_{c}_{s}']=self.df[c].rolling(window=s).mean()
                self.df[f'EMA_{c}_{s}']=self.df[c].ewm(span=s,adjust=False).mean()
        
                if c == 'CLOSE':
                    self.df[f'DIF_EMA_CLOSE_{s}']=self.df['CLOSE']-self.df[f'EMA_CLOSE_{s}']
                    self.df[f'DIF_SMA_CLOSE_{s}']=self.df['CLOSE']-self.df[f'SMA_CLOSE_{s}']
        
    # ema dist metric 
    def calculate_ema_dist(self,cols=['CLOSE'],spans=None):
        cols=cols if cols is not None else self.ma_cols
        spans=spans if spans is not None else self.ma_spans
        for c in cols:
            for s in spans:        
                self.df[f'EMA_DIST_{s}']=(self.df['CLOSE']-self.df[f'EMA_CLOSE_{s}']) / self.df[f'CLOSE']

    def calculate_ema_cumdist(self,cols=['CLOSE'],spans=None,window=100):
        cols=cols if cols is not None else self.ma_cols
        spans=spans if spans is not None else self.ma_spans
        for c in cols:
            for s in spans:        
                self.df[f'CUMDIST_EMA_{s}']=self.df[f'EMA_DIST_{s}'].rolling(window=s).sum()        
                # count for negative positive percentage
                self.df[f'CUMSIGN_EMA_{s}']=self.df[f'EMA_DIST_{s}'].apply(lambda x: -1 if x<0 else 1).rolling(window=s).mean()

        
    # calculates RSI 
    def calculate_rsi(self, column='CLOSE', period=14):
        delta = self.df[column].diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        RS = gain / loss
        self.df['RSI'] = 100 - (100 / (1 + RS))
        
    # calculates MACD 
    def calculate_macd(self, column='CLOSE', fast_period=12, slow_period=26, signal_period=9):
        self.df['EMA_FAST'] = self.df[column].ewm(span=fast_period, adjust=False).mean()
        self.df['EMA_SLOW'] = self.df[column].ewm(span=slow_period, adjust=False).mean()
        self.df['MACD'] = self.df['EMA_FAST'] - self.df['EMA_SLOW']
        self.df['MACD_SIGNAL'] = self.df['MACD'].ewm(span=signal_period, adjust=False).mean()
        self.df['MACD_SIGNUM']=self.df[['MACD','MACD_SIGNAL']].apply(lambda x: 1 if x['MACD']>x['MACD_SIGNAL'] else -1,axis=1)
        
        
    def calculate_percentile_rank(self,indicator_columns=['RSI','MACD']
                                  ,ema_columns=['EMA_DIST','CUMDIST_EMA','DIF_EMA_CLOSE']
                                  ):
        indicator_columns=indicator_columns or self.indicator_columns
        for col in indicator_columns:
            self.df[f'RANK_PERC_{col}']=self.df[col].rank(pct=True)
            #self.df[f'RANK_PERC_{col}'] = self.df[col].apply(lambda x: self.df[col].rank(pct=True)[self.df[col] == x].values[0])
        
        for col in ema_columns:
            for s in self.ma_spans:
                colname=f'{col}_{s}'
                self.df[f'RANK_PERC_{colname}']=self.df[colname].rank(pct=True)
        
    # write calcview back to postgres 
    def write_to_pg(self,**kwargs):
        self.logger.info(f'writing {self.ticker} to pg ')
        cv_name=f'CALC_VIEW_{self.ticker}'
        self.db.write_tmp_df(self.df,cv_name,**kwargs)
        
        
    def make_calcviews(self):
        # query all raw tables 
        query="""
        SELECT table_name
        FROM information_schema.tables
        join "dev"."nasdaq" 
            on table_name = "symbol"
        WHERE table_schema = 'market_stats_raw'
          AND table_type = 'BASE TABLE'
          and table_name !='tmp';
        """
        # query all raw tables without calcviews 
        query="""
                    with RAW_TABLES as ( 
            SELECT T1.table_name
                    FROM information_schema.tables T1
                    WHERE T1.table_schema = 'market_stats_raw'
                      AND T1.table_type = 'BASE TABLE'
                      and T1.table_name !='tmp'
                      and T1.TABLE_NAME not like 'CALC_VIEW%'
            ),CVS as (
            SELECT T1.table_name,REPLACE(T1.TABLE_NAME,'CALC_VIEW_','') as TABLE_NAME2
                    FROM information_schema.tables T1
                    WHERE T1.table_schema = 'dev'
                      AND T1.table_type = 'BASE TABLE'
                      and T1.table_name !='tmp'
                      and T1.TABLE_NAME LIKE 'CALC_VIEW%'
            )
            select * from raw_tables
            where table_name not in ( select table_name2 from cvs);
        """
        self.db.schema='market_stats_raw'
        self.db.connect()
        tickers=self.db.execute_select(query)['table_name'].to_list()
        print(tickers)
        self.db.schema='dev'
        self.db.connect()
        counter=0 
        for t in tickers:
            self.ticker=t
            print(t)
            c.get_data()
            c.calculate_mas()
            c.calculate_rsi()
            c.calculate_macd()
            c.write_to_pg()
            counter+=1 
            if counter>50: # reconnecting to db every 50 tickers
                self.db.close()
                self.db.connect()
                counter=0
        
if __name__=='__main__':
    t='AAPL'
    c=calcview(t)
    c.get_data()
    c.calculate_mas()
    c.calculate_rsi()
    c.calculate_macd()
    c.calculate_ema_dist()
    c.calculate_ema_cumdist()
    c.calculate_percentile_rank()
    c.write_to_pg()
    print(c.df.columns)

    
    exit(1)
    
    
    c.calculate_mas()
    print(c.df.head(100))
    print(c.df.columns)