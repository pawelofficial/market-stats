from abc import ABC, abstractmethod
import pandas as pd 
import os 
import requests

# switch to from app.back.utils import * if you are running this script from main.py
from market_stats.utils import * 
#if __name__=='__main__':
#    from utils import * 
#else:
#    from app.back.utils import * 

class Data(ABC):
    def __init__(self):
        self.this_path = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(self.this_path, 'data')
        self.logger = setup_logger('data',fp=os.path.join(self.this_path,'logs') )
        self.base_columns = ['open', 'close', 'low', 'high','volume']
        self.tickers_map = {'SPX': '^GSPC', 'BTC': 'BTC-USD','BTCUSDT':'BTC'}
        self.logger.info('Data class initialized')
        self.df=None
        self.metadata={}
        
    def save_metadata(self,**kwargs):
        for k,v in kwargs.items():
            self.metadata[k]=v
    
    @abstractmethod
    def download_data(self):
        pass  # Must be implemented by subclasses
    
    
    def save_cache(self,df):
        fp=os.path.join(self.data_path,'cache.csv')
        symbol=self.metadata['symbol']
        interval=self.metadata['interval']
        start_ts=df.iloc[0]['unixtimestamp']
        end_ts=df.iloc[-1]['unixtimestamp']
        filename=self.metadata['filename']
        tmp_df=pd.DataFrame({'symbol':[symbol],'interval':[interval],'start_unixtimestamp':[start_ts],'end_unixtimestamp':[end_ts],'filename':[filename] }  )
        tmp_df.to_csv(fp,index=False,mode='a',header=False)

    def check_cache(self
                    ,symbol
                    ,interval
                    ,start_unixtimestamp
                    ,end_unixtimestamp   # yyyy-mm-dd)
                      ):
        cache_df=pd.read_csv(os.path.join(self.data_path,'cache.csv')).drop_duplicates()

        msk=(cache_df['symbol']==symbol) & (cache_df['interval']==interval) & (cache_df['start_unixtimestamp']<=start_unixtimestamp) & (cache_df['end_unixtimestamp']>=end_unixtimestamp)
        if not cache_df[msk].empty:
            filename=cache_df[msk].iloc[0]['filename']
            df=pd.read_csv(os.path.join(self.data_path,filename))
            # filter out df based on timestamps 
            msk=(df['unixtimestamp']>=start_unixtimestamp) & (df['unixtimestamp']<=end_unixtimestamp)
            df=df[msk]
            if not df.empty:
                return df
        


class BinanceData(Data):
    def __init__(self):
        super().__init__()  # <-- This calls Data's __init__, setting self.data_path
        self.base_columns = ['open', 'close', 'low', 'high','volume']
        self.logger.info('BinanceData class initialized')

    
    def download_data(self
                      ,symbol
                      ,interval='1d'
                      ,startTime = '2021-01-01' # yyyy-mm-dd
                      ,endTime = '2025-01-01'   # yyyy-mm-dd
                      ,save=True
                      ,cleanup=True
                      ):

        self.metadata['symbol']=symbol
        self.metadata['interval']=interval
        self.logger.info(f'downloading data for {symbol} from {startTime} to {endTime}')
        starttime=to_milliseconds(startTime)
        endtime=to_milliseconds(endTime,inclusive=True)

        
        df=self.check_cache(symbol=symbol,interval=interval,start_unixtimestamp=starttime,end_unixtimestamp=endtime)
        if df is not None:
            self.df=df
            print('from cache')
            print(df.iloc[0]['close_datetime'] )
            print(df.iloc[-1]['close_datetime'] )
            print(df)
            return df

        filenames=[]
        while True:
            df=self._get_binance_candles(symbol, interval=interval, limit=500,startTime=starttime,endTime=None)
            start=str(to_datetime(df['unixtimestamp'].iloc[0])).replace(':','_').replace(' ','_')
            end=str(to_datetime(df['unixtimestamp'].iloc[-1])).replace(':','_').replace(' ','_')
            filename = os.path.join(os.path.join(self.data_path,'tmp') , f'{self.tickers_map[symbol]}_{start}_{end}_{interval}.csv')
            df.to_csv(filename)
            
            starttime=df['unixtimestamp'].iloc[-1]+1
            filenames.append(filename)
            assert starttime > endtime or len(df) == 500, 'missing candles'
            if starttime > endtime:
                break
            
        master_df=pd.concat([pd.read_csv(filename) for filename in filenames])
        master_df_filename= f'{self.tickers_map[symbol]}_{startTime}_{endTime}_{interval}.csv'
        self.metadata['filename']=master_df_filename
        master_df.to_csv(os.path.join(self.data_path,master_df_filename))
        
        if save:
            self.df=master_df
        
        if cleanup:
            for filename in filenames:
                os.remove(filename)
        
        self.save_metadata(symbol=symbol,interval=interval,startTime=startTime,endTime=endTime,size=len(master_df))
        self.save_cache(master_df)
        print(len(master_df))
                
    def _get_binance_candles(self,symbol, interval="1m"
                                , limit=1000     # fetches this number of candles
                                , startTime=None # unixtimestamp 
                                , endTime=None  # unixtimestamp 
                                ):
            print('downloading the data ! ')
            url = "https://api.binance.com/api/v3/klines"
            params = {"symbol": symbol, "interval": interval, "limit": limit}
            if startTime:
                params["startTime"] = startTime
            if endTime:
                params["endTime"] = endTime
            response = requests.get(url, params=params)
            response.raise_for_status()
            candles = response.json()

            # Format each candle as a list
            formatted_candles= [
                [
                    candle[0],    # Open time
                    candle[1],    # Open price
                    candle[2],    # High price
                    candle[3],    # Low price
                    candle[4],    # latest price / close price 
                    candle[5],    # Volume
                    candle[6],    # Close time
                    candle[7],    # Quote asset volume
                    candle[8],    # Number of trades
                    candle[9],    # Taker buy base asset volume
                    candle[10],   # Taker buy quote asset volume
                    candle[11]    # Ignore
                ]
                for candle in candles
            ]


            dic={'unixtimestamp':formatted_candles[0][0]
                 ,'close_time':formatted_candles[0][6]
                 ,'datetime':pd.to_datetime(formatted_candles[0][0],unit='ms')
                 ,'close_datetime':pd.to_datetime(formatted_candles[0][6],unit='ms')
                 ,'open':formatted_candles[0][1]
                 ,'close':formatted_candles[0][4]
                 ,'low':formatted_candles[0][3]
                 ,'high':formatted_candles[0][2]
                 ,'volume':formatted_candles[0][5]
                 }
            df=pd.DataFrame(columns=list(dic.keys()))
            for candle in formatted_candles:
                dic={'unixtimestamp':candle[0]
                     ,'close_time':candle[6]
                     ,'datetime':pd.to_datetime(candle[0],unit='ms')
                     ,'close_datetime':pd.to_datetime(candle[6],unit='ms')
                     ,'open':candle[1]
                     ,'close':candle[4]
                     ,'low':candle[3]
                     ,'high':candle[2]
                    ,'volume':candle[5]
                     }
                df.loc[len(df)]=dic


            # cast base columns to float
            for col in self.base_columns:
                df[col]=df[col].astype(float)


            return df


# obj = MyAbstractClass()  # Would raise an error

if __name__=='__main__':
    
    obj=BinanceData()
    obj.download_data('BTCUSDT',interval='1d',startTime='2020-01-01',endTime='2025-01-01',save=True)
    print(obj.metadata)
