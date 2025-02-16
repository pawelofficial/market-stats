import streamlit as st 
import market_stats as ms
import pandas as pd 


def use_cache(key,fun,*args,**kwargs):
    if key not in st.session_state or st.session_state[key] is None:
        st.session_state[key] =  fun
        return st.session_state[key]
    return st.session_state[key]


db=use_cache('db',ms.Database )

#counts in cv_all
query="""
WITH cv_cte AS ( 
select "TICKER",MAX("TS") as max_ts, min("TS") as min_ts
, count(*) as cnt  
from "dev"."CV_ALL" group by "TICKER" order by min("TS") asc 
)
,is_cte AS ( 
        SELECT table_name, "symbol",s.n_live_tup AS row_count
        FROM "market_stats_raw"."nasdaq"  
        left join information_schema.tables t  
            on table_name = "symbol"
        FULL outer JOIN  pg_stat_user_tables s 
    		ON t.table_name = s.relname
    		and t.table_schema=s.schemaname
        WHERE table_schema = 'market_stats_raw'
           and table_name !='tmp'
           AND table_type = 'BASE TABLE'
          order by "row_count"
)
SELECT "TICKER","table_name", "cnt","row_count" AS "raw_cnt","min_ts","max_ts",  "row_count"-"cnt" AS "dif"
	FROM is_cte 
		FULL OUTER JOIN  cv_cte 
			ON is_cte."table_name"="cv_cte"."TICKER"
"""

df=db().execute_select(query)

def highlight_counts(s):
    return ['background-color: green' if v==0 else 'background-color: red' if pd.isnull(v) else 'background-color: orange' for v in s]


# Apply the styling to the DataFrame
styled_df = df.style.apply(highlight_counts, subset=['dif'], axis=1)

# Display the styled DataFrame
st.markdown('1 data in cv_all vs data in market_stats_raw for nasdaq tables')
st.dataframe(styled_df)


# does cv all contain all nasdaq symbols 
query="""
SELECT DISTINCT "TICKER","symbol"
	FROM "dev"."CV_ALL"
		FULL OUTER JOIN "market_stats_raw"."nasdaq" 
			ON "CV_ALL"."TICKER"="nasdaq"."symbol"
	ORDER BY "TICKER" NULLS FIRST 
"""
df=db().execute_select(query)

def highlight_counts(s):
    return ['background-color: red'  if pd.isnull(v) else 'background-color: green' for v in s]

styled_df = df.style.apply(highlight_counts, subset=['TICKER'], axis=1)
st.markdown("2 missing nasdaq symbols in cv_all")
st.dataframe(styled_df)



# inconsistent counts in cv_all
query="""
WITH cte AS  (
SELECT "TICKER",count(*) AS "cnt",min("TS") AS min_ts, max("TS") AS max_ts 
FROM "dev"."CV_ALL"
GROUP BY "TICKER"
) SELECT "TICKER","cnt","min_ts","max_ts"
	,"cnt"=(SELECT max("cnt") FROM cte ) AS is_max_rows
FROM cte 
ORDER BY is_max_rows ASC
"""

df=db().execute_select(query)

def highlight_counts(s):
    return ['background-color: green'  if v else 'background-color: red' for v in s]
            
styled_df = df.style.apply(highlight_counts, subset=['is_max_rows'], axis=1)
st.markdown("3 are row counts equal in cv_all for tickers")
st.dataframe(styled_df)