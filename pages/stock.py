import streamlit as st 
from market_stats.db import * 
from market_stats.plots import * 
from market_stats.calcview import *
from market_stats.statsview import *
from market_stats.get_data import *
from market_stats.utils import setup_logger,exception_logger
import time 
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker  # Rename ticker to avoid conflicts


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


        fig,axes,df=make_my_plot(
        ticker = ticker
        ,plotname = None 
        ,datefrom = '2020-01-01' 
        ,emas=UI_METRIC_TO_CONFIG_MAP[metric]
        ,indicators=UI_METRIC_TO_INDICATOR_MAP[indicator]
        )

        # show fig 
        st.pyplot(fig)
        return df 


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



def compute_integrals(df):
    # Compute the integral of the curve using actual x, y values
    integrals = {}
    for span in [5, 10, 20, 50, 100]:
        # calculation of integral: 
        #x_values = df['ID'][:span] 
        #y_values = df['CLOSE_NORM'][:span] 
        #integral = np.trapz(y_values, x=x_values)
        #integral = integral - y_values.iloc[0]  # subtract the initial value
        
        # this shouldnt be an integral but last value minus first value 
        x_values = df['ID'][:span].values 
        y_values = df['CLOSE_NORM'][:span].values 
        integral=y_values[-1]/y_values[0]

        integrals[f'span_{span}'] = np.round(integral,2)

    integrals['avg']=np.mean(list(integrals.values()))
    integrals['min']=np.min(list(integrals.values()))
    integrals['max']=np.max(list(integrals.values()))
    return integrals


def make_gains_plot(ticker,metric,cutoff,base_df):
    with st.spinner('Making gains plot...'):
        df=StatsView().gains_query(ticker,metric,cutoff)
        fig,ax=plt.subplots(1,1)
        # for each value of GID2 plot df with different color 
        integrals_dic={}
        n=0
        for gid in df['GID2'].unique():
            df_=df[df['GID2']==gid]
            ax.plot(df_['GID'],df_['CLOSE_NORM'],'-')
            integrals=compute_integrals(df_)
            integrals_dic[f'curve_{gid}']=integrals
            n+=1
                    # Place the label at the end of each curve
            ax.text(df_['GID'].iloc[-1], df_['CLOSE_NORM'].iloc[-1], f"Curve {n}", 
                verticalalignment='center', horizontalalignment='left')

        #_=list(integrals_dic.keys()) [0]
        #integrals_dic['agg']={k:0 for k in integrals_dic[_] .keys()}
        integrals_df=pd.DataFrame(integrals_dic).T
        integrals_df.loc['mean'] = integrals_df.iloc[:-1].mean()
 

        

        
        st.write(f"for ticker {ticker} with cutoff value of {metric} = {cutoff} following {n} gain curves were observed")
        st.pyplot(fig)
        
        fig,ax=plt.subplots(1,1)
        n=0
        ax.plot(base_df['TS'],base_df['Close'],'.k')
        ax2 = ax.twinx()

        # Mask the data based on the cutoff
        above_cutoff = base_df[metric].where(base_df[metric] > cutoff, np.nan)
        below_cutoff = base_df[metric].where(base_df[metric] <= cutoff, np.nan)

        # Plot the data with conditional coloring
        ax2.plot(base_df['TS'], above_cutoff, '-g')  # Green for above cutoff
        ax2.plot(base_df['TS'], below_cutoff, '-r')  # Red for below cutoff (optional, can be removed)
        
        # Set the secondary y-axis gridlines to show 10 equally spaced lines
        y_min, y_max = ax2.get_ylim()  # Get the current y-axis limits
        interval = (y_max - y_min) / 20  # Calculate the interval for 10 lines
        ax2.yaxis.set_major_locator(mticker.MultipleLocator(interval))
        ax2.grid(True, which='both')  # Ensure gridlines are shown for the secondary axis

        n=0

        for gid in df['GID2'].unique():
            logging.info(df_.columns)
            print(df_.columns)
            df_=df[df['GID2']==gid]

            #ax.plot(df_['TS'],df_['CLOSE'],'-',label=f"Curve {n}")
            n+=1
        #ax.legend()
        
        st.write(f"Price action chart for {ticker} with cutoff value of {metric} = {cutoff} gain curves and underlying metric")
        st.pyplot(fig)
        return integrals_df
        
        
        


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
    df=make_plot(ticker,plot_indicator,plot_metric)

# histogram plot 
#    rank_perc_metrics=[i.replace('RANK_PERC_','') for i in metric_cols if 'RANK_PERC' in i]
#    hist_metric=st.selectbox('select histogram metric',rank_perc_metrics,0)
#    make_histogram_plot(hist_metric,ticker)
    
# gains plot 
    gains_metric=st.selectbox('select gains metric',metric_cols,metric_cols.index('CUMDIST_EMA_100'))
    gains_cutoff=st.number_input('select gains cutoff',-9999.0,9999.0,-2.5,0.1)
    integrals_df=make_gains_plot(ticker,gains_metric,gains_cutoff,df)
    # put agg rows as first 
    integrals_df=integrals_df.reindex(['mean']+list(integrals_df.index[:-1]))

    
 
    st.write(f"if you bought {ticker} at {gains_metric}={gains_cutoff} you would have make following gains")
    st.write(integrals_df)