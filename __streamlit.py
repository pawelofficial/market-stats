import streamlit as st 
from db import * 
from plots import * 
from calcview import *
from statsview import *
from get_data import *
from utils import setup_logger,exception_logger
import time 
import matplotlib.pyplot as plt


streamlit_logger=setup_logger('streamlit',fp='./logs/',mode='w')

def init_session_state(
    vars=['db','db_con_time','nasdaq_symbols','first_run']):

    # initiate as none 
    for v in vars:
        streamlit_logger.info(f'initializing {v}')
        st.session_state[v]=None

    # populate 
    for v in vars:
        if v =='nasdaq_symbols':
            st.session_state[v]=data().get_nasdaq_symbols()
        if v=='first_run':
            st.session_state[v]=True


def connect_to_db():
    if st.session_state.db is None or st.session_state.db.closed or (time.time()-st.session_state['db_con_time'])>300:
        streamlit_logger.info('connecting to db')
        st.session_state['db']=Database()
        st.session_state['db'].connect()
        st.session_state['db_con_time']=time.time()
        

# sidebar 
def make_sidebar():
    st.sidebar.title("Sidebar Title")  # Provide a title for the sidebar



def show_df(metric):
    st.write(f'Tickers with lowest {metric}')
    UI_TO_PG_MAP={
        'RSI':'RSI',
        'MACD':'MACD',
        'EMA Distance':'EMA_DIST'
        ,'Cumulative EMA distance 10':'CUMDIST_EMA_10'
        ,'Cumulative EMA distance 20':'CUMDIST_EMA_20'
        ,'Cumulative EMA distance 50':'CUMDIST_EMA_50'
        ,'Cumulative EMA distance 100':'CUMDIST_EMA_100'
        , 'EMA Distance 10':'EMA_DIST_10'
        , 'EMA Distance 20':'EMA_DIST_20'
        , 'EMA Distance 50':'EMA_DIST_50'
        , 'EMA Distance 100':'EMA_DIST_100'
        , 'Cumulative EMA Sign 10':'CUMSIGN_EMA_10'
        , 'Cumulative EMA Sign 20':'CUMSIGN_EMA_20'
        , 'Cumulative EMA Sign 50':'CUMSIGN_EMA_50'
        , 'Cumulative EMA Sign 100':'CUMSIGN_EMA_100'
    }
    metric=UI_TO_PG_MAP[metric]
    
    if metric is None:
        return 
    if metric=='RSI':
        df=StatsView().stats_query_1(metric='RSI',top_n=10,lowest=True)
    else:
        df=StatsView().stats_query_1(metric=metric,top_n=10,lowest=True)

    # put ticker as first column
    cols=df.columns.tolist()
    cols.remove('TICKER')
    cols.remove(metric)
    cols.insert(0,metric)
    cols.insert(0,'TICKER')
    df=df[cols]
    st.write(df)
    return df['TICKER'].tolist()[0]


def make_plot(ticker,indicator,metric):
    with st.spinner('Making plot...'):
        UI_METRIC_TO_CONFIG_MAP={
            'EMA':{'name':'EMA_CLOSE', 'spans': [10,20,50,100],'secondary_y':False}
            ,'EMA Distance':{'name':'EMA_DIST', 'spans': [10,20,50,100],'secondary_y':True}
            ,'Cumulative EMA distance':{'name':'CUMDIST_EMA', 'spans': [10,20,50,100],'secondary_y':True}
            ,'Cumulative EMA Sign':{'name':'CUMSIGN_EMA', 'spans': [10,20,50,100],'secondary_y':True}
        }
        UI_METRIC_TO_INDICATOR_MAP={
            'RSI':['RSI']
            ,'MACD':['MACD','MACD_SIGNAL','MACD_SIGNUM']
        }


        fig,axes=make_my_plot(
        ticker = ticker
        ,plotname = None 
        ,datefrom = '2020-01-01' 
        ,emas=UI_METRIC_TO_CONFIG_MAP[metric]
        ,indicators=UI_METRIC_TO_INDICATOR_MAP[indicator]
        )

        # show fig 
        st.pyplot(fig)
    

def make_histogram_plot(metric,ticker):
    METRIC_TO_PG_MAP={
        'RSI':'RANK_PERC_RSI',
        'MACD':'RANK_PERC_MACD',
        'EMA Distance':'RANK_PERC_EMA_DIST'
        ,'Cumulative EMA distance 10':'RANK_PERC_CUMDIST_EMA_10'
        ,'Cumulative EMA distance 20':'RANK_PERC_CUMDIST_EMA_20'
        ,'Cumulative EMA distance 50':'RANK_PERC_CUMDIST_EMA_50'
        ,'Cumulative EMA distance 100':'RANK_PERC_CUMDIST_EMA_100'
        , 'EMA Distance 10':'RANK_PERC_EMA_DIST_10'
        , 'EMA Distance 20':'RANK_PERC_EMA_DIST_20'
        , 'EMA Distance 50':'RANK_PERC_EMA_DIST_50'
        , 'EMA Distance 100':'RANK_PERC_EMA_DIST_100'
        , 'Cumulative EMA Sign 10':'RANK_PERC_CUMSIGN_EMA_10'
        , 'Cumulative EMA Sign 20':'RANK_PERC_CUMSIGN_EMA_20'
        , 'Cumulative EMA Sign 50':'RANK_PERC_CUMSIGN_EMA_50'
        , 'Cumulative EMA Sign 100':'RANK_PERC_CUMSIGN_EMA_100'
    }
    with st.spinner('Making histogram plot...'):
        percentile,last_value,data=StatsView().histogram_query_1(metric,ticker,value='last')
        fp=make_my_histogram(data,last_value,percentile,metric)
        # display png from fp 
        st.image(fp)
    

def make_gains_plot(ticker,metric,cutoff):
    with st.spinner('Making gains plot...'):
        df=StatsView().gains_query(ticker,metric,cutoff)
        fig,ax=plt.subplots(1,1)
        # for each value of GID2 plot df with different color 
        n=0
        for gid in df['GID2'].unique():
            df_=df[df['GID2']==gid]
            ax.plot(df_['GID'],df_['CLOSE_NORM'],'-')
            n+=1
        #ax.plot(df['GID'],df['CLOSE_NORM'],'-')
        
        st.write(f"for ticker {ticker} with cutoff value of {metric} = {cutoff} following {n} gain curves were observed")
        st.pyplot(fig)
        
        
init_session_state()
connect_to_db()
make_sidebar()
st.title('Market Stats')

# Use the cached connection to execute the query

# dropdown to select ticker
df_indicator = st.sidebar.selectbox('Dataframe Metric', ['RSI', 'MACD'
                                        , 'EMA Distance 10'
                                        ,'Cumulative EMA distance 10'
                                        ,'Cumulative EMA Sign 10'
                                        , 'EMA Distance 20'
                                        ,'Cumulative EMA distance 20'
                                        ,'Cumulative EMA Sign 20'
                                        , 'EMA Distance 50'
                                        ,'Cumulative EMA distance 50'
                                        ,'Cumulative EMA Sign 50'
                                        , 'EMA Distance 100'
                                        ,'Cumulative EMA distance 100'
                                        ,'Cumulative EMA Sign 100'

                                        ],index=0,key='df_indicator')
# call show_df


# dropdown for making a plot 

# find index of df ticker that is on top 
ticker_of_interest=show_df(df_indicator)
index_of_ticker_of_interest=st.session_state['nasdaq_symbols'].index(ticker_of_interest)

plot_ticker=st.sidebar.selectbox('Plot Ticker',st.session_state['nasdaq_symbols'],index=index_of_ticker_of_interest)

plot_indicator = st.sidebar.selectbox('Plot Metric', ['RSI', 'MACD'
                                        ],index=1,key='plot_indicator')

plot_metric = st.sidebar.selectbox('Plot Metric', [
                                        'EMA'
                                        ,'EMA Distance'
                                        ,'Cumulative EMA distance'
                                        ,'Cumulative EMA Sign'
                                    
                                        ],index=2,key='plot_metric')


plot_histogram=st.sidebar.selectbox('Histogram - last value of', ['RSI', 'MACD'
                                        , 'EMA Distance 10'
                                        ,'Cumulative EMA distance 10'
                                        ,'Cumulative EMA Sign 10'
                                        , 'EMA Distance 20'
                                        ,'Cumulative EMA distance 20'
                                        ,'Cumulative EMA Sign 20'
                                        , 'EMA Distance 50'
                                        ,'Cumulative EMA distance 50'
                                        ,'Cumulative EMA Sign 50'
                                        , 'EMA Distance 100'
                                        ,'Cumulative EMA distance 100'
                                        ,'Cumulative EMA Sign 100'

                                        ],index=0,key='plot_histogram')

# plot button 
#if st.sidebar.button('Plot again'):
#    make_plot(plot_ticker,plot_indicator,plot_metric)



#if st.session_state['first_run']:
#st.session_state['first_run']=False
#make_plot(plot_ticker,plot_indicator,plot_metric)
#make_histogram_plot(plot_histogram,plot_ticker)
make_gains_plot("AAPL", 'RSI',20)
    