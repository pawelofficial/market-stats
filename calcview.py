from db import *


class calcview:
    def __init__(self, ticker):
        self.ticker=ticker 
        self.db=Database()
        self.limit =''
        self.df=None
        self.ma_cols=['OPEN','HIGH','LOW','CLOSE']
        self.ma_spans=[5,10,20,50,100,200]
        
    def get_data(self,ticker = None ,limit = None ):
        if self.db.is_connected==False:
            self.db.connect()
        ticker=ticker if ticker is not None  else self.ticker
        limit=f'limit {limit}' if limit is not None else self.limit
        self.df=self.db.execute_select(f'select * from {ticker} {limit} ' )
        # capitalize column names
        self.df.columns=[col.upper() for col in self.df.columns]
        
    # aggregate to span in seconds 

        
        
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
        
        
if __name__=='__main__':
    c=calcview('AAPL')
    c.get_data()
    c.calculate_mas()
    print(c.df.head(100))
    print(c.df.columns)