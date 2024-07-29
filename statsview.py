from db import Database
import numpy as np 

class StatsView(Database):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect()
        # Additional initialization for statsview
        
        
    def make_cv_all(self):
        # combines all calcviews into single view 
        query="""
        SELECT table_name
        FROM information_schema.tables t
        JOIN pg_stat_user_tables s
          ON t.table_name = s.relname
        join "market_stats_raw"."nasdaq"
            on replace(table_name,'CALC_VIEW_','')  ="symbol" -- use only nasdaq tables 
        WHERE t.table_schema = 'dev'
          AND t.table_type = 'BASE TABLE'
          AND t.table_name LIKE 'CALC_VIEW%'
          AND s.n_live_tup > 0;
        """
        df=self.execute_select(query)
        cv_views=df['table_name'].tolist()
        
        # union all cv views into one view 
        drop_query="drop view if exists CV_ALL;"
        self.execute_dml(drop_query)
        
        query2=f'create or replace view "CV_ALL" as '
        for cv in cv_views:
            query2+=f'select * from "{cv}" union all '
        query2=query2[:-10]
        
        # write to a tmp table
        print(query2)
        self.execute_dml(query2)
                
    # returns lowest/highest tickers for a given metric
    def stats_query_1(self,metric="RSI",top_n=10,lowest=True
                      ,drop_cols=['ID','dr','dr_ts']
                      ):
 
        # query getting stats
        query=f"""
        with last_data as (
            select *, dense_rank() over ( partition by "TICKER" order by "TS" desc ) dr_ts 
            from "CV_ALL"
            where "TS" = (select max("TS") from "CV_ALL")
            ), cte AS (
                SELECT *, 
                       DENSE_RANK() OVER (ORDER BY "{metric}" {"asc" if lowest else "desc"}  ) AS dr
                FROM last_data 
            	where dr_ts = 1 
                )
            SELECT *
            FROM cte 
            WHERE dr <={top_n}
            --AND "RSI"!=0.0
            ORDER BY "{metric}";
        """
        
        df=self.execute_select(query) 
        # drop drop_cols 
        df=df[[c for c in df.columns if c not in drop_cols]]
        
        # write df to pgsql 
        self.write_tmp_df(df,'stats_query_1')
        return df 
    
    def histogram_query_1(self,metric,ticker,value='last'):
        def calculate_percentile(data, value):
            sorted_data = sorted(data)
            percentile = np.searchsorted(sorted_data, value, side='right') / len(sorted_data) * 100
            return percentile
        query=f"""
        select "{metric}" as metric from "dev"."CV_ALL"
        """
        l=self.execute_select(query)['metric'].tolist()
        # query for taking last value for specific ticker 
        query=f"""
        select "{metric}" as metric, "RANK_PERC_{metric}" as percentile_metric from "CV_ALL" where "TICKER"='{ticker}' and "TS"=(select max("TS") from "CV_ALL" where "TICKER"='{ticker}')
        """
        df=self.execute_select(query)

        last_value=df.iloc[0]['metric']
        percentile=df.iloc[0]['percentile_metric']
        
        return percentile,last_value,l
        
        

if __name__=='__main__':
    s= StatsView()
    
    #s.make_cv_all()

    df=s.execute_select('select "CLOSE" from "dev"."islands"')['CLOSE'].tolist()
    # plot data on regular line chart 
    import matplotlib.pyplot as plt
    plt.plot(df)
    plt.show()

    ##df['RANK_PERC_RSI']=df['RSI'].rank(pct=True)
#
    ## plot histogram of data 
    #import matplotlib.pyplot as plt
    #plt.hist(df,bins=100)
    #plt.show()