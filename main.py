
from get_data import * 
from calcview import * 
from statsview import *
# 1 download some data 




#tickers=tickers[:3]
do_one=False
if do_one:
    d=data()
    d.db.connect()
    nasdaq_symbols=d.get_nasdaq_symbols()
    
    d.db.execute_dml('drop schema market_stats_raw cascade') # rememebr to make nasdaq table manually
    d.db.execute_dml('create schema market_stats_raw')
    d.db.schema='market_stats_raw'
    
    for t in nasdaq_symbols:
        
        d.db.create_or_replace_ticker_table(t)
        d.download_historical_data(tgt_table=t,ticker=t,start_ts='2020-01-01',end_ts='today',interval='1d')


# 2 build calc views on data 
do_two=True
if do_two:
    d=data()
    
    d.db.connect()
    d.db.execute_dml('drop schema dev cascade')
    d.db.execute_dml('create schema dev')

    tables=d.get_raw_tables()
    print(tables,len(tables))

    for t in tables:
        print(t)
        c=calcview(t)
        c.get_data()
        c.calculate_mas()
        c.calculate_rsi()
        c.calculate_macd()
        c.calculate_ema_dist()
        c.calculate_ema_cumdist()
        c.calculate_percentile_rank()
        c.write_to_pg(drop=False)
        #exit(1)


s=StatsView()
s.make_cv_all()
df=s.stats_query_1(metric="RSI",top_n=5,lowest=True)
print(df)

    # metric 
    # sort by metric 
    # plot your metric
    # backtest on your metric