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
bd.download_data('BTCUSDT',interval='1d',startTime='2024-01-01',endTime='2025-01-01',save=True)
p=Plotter(bd.df)
plot_fp=p.candleplot2(interval='1d',asset='BTC',df=bd.df,ser=None,date_column='datetime',save=True,show=False)
# show plot 
st.image(plot_fp)
st.write(bd.metadata)
