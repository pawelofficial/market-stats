import streamlit as st 
from market_stats.db import * 
from market_stats.plots import * 
from market_stats.calcview import *
from market_stats.statsview import *
from market_stats.get_data import *
from market_stats.utils import setup_logger,exception_logger
import time 
import matplotlib.pyplot as plt


stock_logger=setup_logger('stock',fp='./logs/',mode='w')

def init_session_state(
    vars=['db','db_con_time','nasdaq_symbols','first_run']):

    # initiate as none 
    for v in vars:
        stock_logger.info(f'initializing {v}')
        st.session_state[v]=None

    # populate 
    for v in vars:
        if v =='nasdaq_symbols':
            st.session_state[v]=data().get_nasdaq_symbols()
        if v=='first_run':
            st.session_state[v]=True


def connect_to_db():
    if st.session_state.db is None or st.session_state.db.closed or (time.time()-st.session_state['db_con_time'])>300:
        stock_logger.info('connecting to db')
        st.session_state['db']=Database()
        st.session_state['db'].connect()
        st.session_state['db_con_time']=time.time()
        

def execute_or_get_from_cache(key,fun,*args,**kwargs):
    if key not in st.session_state or st.session_state[key] is None:
        stock_logger.info(f'executing {fun.__name__}')
        st.session_state[key] =  fun(*args,**kwargs)
        return st.session_state[key]
    stock_logger.info(f'getting {key} from cache')
    return st.session_state[key]




# DISPLAYS A DF AND A SELECTOR FOR A METRIC THAT YOU WANT TO TAKE A CLOSER LOOK AT 
def show_df():
    UI_TO_PG_MAP={
        'RSI':'RSI'
        ,'MACD':'MACD'
        ,'EMA Distance 10':'EMA_DIST_10'
        ,'EMA Distance 20':'EMA_DIST_20'
        ,'EMA Distance 50':'EMA_DIST_50'
        ,'EMA Distance100':'EMA_DIST_100'
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
    
    metric=st.selectbox('select metric ',list(UI_TO_PG_MAP.keys()) )
    pgmetric=UI_TO_PG_MAP[metric]
    df=StatsView().stats_query_1(metric=pgmetric,top_n=None,lowest=True) # this df cant be cached because there dense rank on metric 
    cols=df.columns.tolist()
    cols.remove('TICKER')
    cols.remove(pgmetric)
    cols.insert(0,pgmetric)
    cols.insert(0,'TICKER')
    df=df[cols]
    df=df.sort_values(by=pgmetric)
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
    #metric=METRIC_TO_PG_MAP[metric]
    with st.spinner('Making histogram plot...'):
        percentile,last_value,data=StatsView().histogram_query_1(metric,ticker,value='last')
        fp=make_my_histogram(ticker,data,last_value,percentile,metric)
        # display png from fp 
        st.image(fp)
        
        percentile,last_value,data=StatsView().histogram_query_1(metric,'All',value=last_value)
        fp=make_my_histogram('All',data,last_value,percentile,metric)
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
        

        fig,ax=plt.subplots(1,1)
        # for each value of GID2 plot df with different color 
        n=0
        ax.plot(df['ID'],df['CLOSE'],'.k')
        for gid in df['GID2'].unique():
            df_=df[df['GID2']==gid]
            ax.plot(df_['ID'],df_['CLOSE'],'-')
            n+=1
        # plot metric on secondary axis


        
        st.write(df)
        
        st.write(f"for ticker {ticker} with cutoff value of {metric} = {cutoff} following {n} gain curves were observed")
        st.pyplot(fig)
        


if __name__=='__main__':
    init_session_state()

    #db=execute_or_get_from_cache('db',connect_to_db)
    db=Database()
    db.connect()
    
    
    nasdaq_tickers=data().get_nasdaq_symbols()
#
    show_df()
#
    cv_columns=db.execute_select(''' 
                                 SELECT column_name
                                FROM information_schema.columns
                                WHERE table_name = 'CV_ALL';
                                 ''')
    base_cols,metric_cols=calcview('foo').get_base_columns()
    indicator_columns=calcview('foo').indicator_columns



# select stock 
    ticker=st.selectbox('select stock',st.session_state['nasdaq_symbols'],st.session_state['nasdaq_symbols'].index('AAPL')  )
 
# metrics plot 
    plot_metrics=['EMA','EMA Distance','Cumulative EMA distance','Cumulative EMA Sign'] # would be nice to gather them from calcview 
    plot_metric=st.selectbox('select metric',plot_metrics,2)
    plot_indicator=st.selectbox('select indicator',indicator_columns,0)    
    make_plot(ticker,plot_indicator,plot_metric)

# histogram plot 
#    rank_perc_metrics=[i.replace('RANK_PERC_','') for i in metric_cols if 'RANK_PERC' in i]
#    hist_metric=st.selectbox('select histogram metric',rank_perc_metrics,0)
#    make_histogram_plot(hist_metric,ticker)
    
# gains plot 
    gains_metric=st.selectbox('select gains metric',metric_cols,metric_cols.index('CUMDIST_EMA_100'))
    gains_cutoff=st.number_input('select gains cutoff',-9999.0,9999.0,-2.5,0.1)
    make_gains_plot(ticker,gains_metric,gains_cutoff)
    