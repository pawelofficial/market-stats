import sys 
import os 
import streamlit as st
from datetime import datetime,timedelta
from streamlit_date_picker import date_range_picker, date_picker, PickerType
import time 

# add two dirs above to the path 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import market_stats as ms 

# init session_state
def init_session_state(l=['start','end','cancel','db']):
    for i in l:
        if i not in st.session_state:
            st.session_state[i]=None
# clear session_state
def clear_session_state():
    for i in st.session_state:
        del st.session_state[i]
    st.rerun()

# puts fun into a cache or returns it if it's there 
def use_cache(key,fun,*args,**kwargs):
    if key not in st.session_state or st.session_state[key] is None:
        st.session_state[key] =  fun
        return st.session_state[key]
    return st.session_state[key]


def cancel_download():
    st.session_state['cancel'] = True

init_session_state()
st.write(st.session_state)




# button for clearing session state 
if st.button('clear choices'):
    clear_session_state()


# Initialize the database
db = use_cache('db', ms.Database)()


# Fetch the latest date from the database and convert it to a datetime object
last_date_ts = db.execute_select('select max("TS") as t from "dev"."CV_ALL"')['t'].to_list()[0]
last_date = last_date_ts.to_pydatetime() -timedelta(days=3) # substract to make sure no data is missing
# Set the default start and end dates
start, end = last_date, datetime.now()

# another date picker 
st.markdown("Choose start date")
start = date_picker(picker_type=PickerType.date, key='start', value=start)
st.markdown("Choose end date")
end = date_picker(picker_type=PickerType.date, key='end', value=end)

stocks=ms.data().get_nasdaq_symbols()
stocks.insert(0,'All')

# multiple choice selector
st.session_state['selected_stocks'] = st.multiselect('hoose stocks to sync data', stocks, default=stocks[0] )

# button for downloading data 
if st.button('sync data'):
    with st.spinner('syncing data ...'):
        if 'All' in st.session_state['selected_stocks']:
            selected_stocks = stocks
        else:
            selected_stocks = st.session_state['selected_stocks']
        
        placeholder = st.empty()
        placeholder_button = st.empty()
        
        for no, t in enumerate(selected_stocks):
            if t=='All':
                continue
            placeholder.markdown(f'downloading data for {t} {no + 1}/{len(selected_stocks)}')
            time.sleep(1)
            
            # Cancel button
            if placeholder_button.button('cancel', on_click=cancel_download,key=f'cancel_{no}'):
                break
            
            # Check if cancel button was pressed
            if st.session_state['cancel']:
                placeholder.markdown('Download cancelled')
                # delete keys from session_state
                for k in st.session_state:
                    if k.startswith('cancel_'):
                        del st.session_state
                break
            
            # Uncomment the following line to download historical data
            ms.data().download_historical_data(tgt_table=t, ticker=t, start_ts=start, end_ts=end, interval='1d')
        
        if not st.session_state['cancel']:
            placeholder.markdown('done')
            
# sync calc views 