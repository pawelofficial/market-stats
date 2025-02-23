import streamlit as st 
import sys
from pathlib import Path

# Get the parent directory (where "back" is located)
sys.path.append(str(Path(__file__).resolve().parent.parent))

# example usage 
# streamlit run .\market_stats\dashboard.py

# Now you can import from "back"
from market_stats.data import *
from market_stats.plotter import * 

bd=BinanceData()

# startTime, endTime selector
st.write('Select the start and end time for the data')
start_time=st.date_input('Start Time',value=pd.to_datetime('2024-01-01'))
end_time=st.date_input('End Time',value=pd.to_datetime('2025-01-01'))
# cast to string 


bd.download_data('BTCUSDT',interval='1d',startTime=start_time.strftime('%Y-%m-%d'),endTime=end_time.strftime('%Y-%m-%d'),save=True)
p=Plotter(bd.df)
plot_fp=p.candleplot2(interval='1d',asset='BTC',df=bd.df,ser=None,date_column='datetime',save=True,show=False)
# show plot 
st.image(plot_fp)
st.write(bd.metadata)
