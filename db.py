from utils import setup_logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import pandas as pd 
import json 
from sqlalchemy import create_engine, MetaData
import os 


class Database:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(current_dir, 'logs')
        self.host = '127.0.0.1'
        self.database = 'dev'
        self.schema='market_stats'
        self.user = 'postgres'
        self.password = 'admin'
        # THIS FILE PATH 
        self.logger = setup_logger('db',fp=logs_dir)
        self.port = "5433"
        self.engine = None
        self.session = None
        self.is_connected = False

    def connect(self):
        self.logger.info("Connecting to PostgreSQL")
        try:
            self.engine = create_engine(f'postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?options=-csearch_path%3Ddbo,{self.schema}')
            #metadata = MetaData(schema="dev")
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
        # Set default schema
            #with self.engine.connect() as connection:
            #    connection.execute(f"SET search_path TO {self.schema}")
            self.is_connected = True
            self.logger.info("Connected to PostgreSQL successfully")
        except Exception as error:
            self.logger.error(f"Error while connecting to PostgreSQL {error}")

    def execute_select(self, query,nfetch = None ):
        query=text(query)
        self.logger.info(f"Executing query: {query}")
        if not self.engine:
            self.logger.error("You must connect to the database first")
            return None 
        if nfetch is None:
            result = self.session.execute(query)
        else:
            result = self.session.execute(query).fetchmany(nfetch)
        # cast result to df 
        result=pd.DataFrame(result.fetchall(), columns=result.keys())
        
        self.logger.info(f"Query executed successfully, got df of shape {result.shape}")
        return result

    def execute_dml(self, query):
        query=text(query)
        self.logger.info(f"Executing query: {query}")
        if not self.engine:
            self.logger.error("You must connect to the database first")
            return None 
        try:
            self.session.execute(query)
            self.session.commit()
            self.logger.info("Query executed successfully")
        except Exception as error:
            self.logger.error(f"Error while executing query {error}")
            self.connect()


    # writes df to a tmp table 
    def write_tmp_df(self, df, table_name='tmp_table'):
        if not self.engine:
            self.logger.error("You must connect to the database first")
            return None
        try:
            df.to_sql(table_name, self.engine, if_exists='replace', index=False)
            self.logger.info(f"DataFrame written to {table_name} successfully.")
        except Exception as error:
            self.logger.error(f"Error while writing to PostgreSQL {error}")


    def read_queries(self,queries_fp='./queries.txt'):
        with open(queries_fp) as f:
            txt=f.readlines()
        txt=''.join([line.strip() for line in txt])
        queries = json.loads(txt)
        return queries
    
    def create_or_replace_ticker_table(self,ticker):
        dic=self.read_queries()['query1']
        
        for k,v in dic.items():
            if 'sql' in k:
                v=v.replace('tickers',ticker)
                self.execute_dml(v)
    
    
    def execure_queries(self,dic):    
        for k,v in dic.items():
            if v['type']=='dml':
                self.logger.info(f"Executing query {k}")
                self.execute_dml(v['pre_sql'])
                self.execute_dml(v['sql'])
                self.execute_dml(v['post_sql'])
            else:
                pass 

    def close(self):
        if self.session:
            self.session.close()
            self.logger.info("PostgreSQL session is closed")
            
if __name__=='__main__':
    db=Database()
    db.connect()
    d=db.create_or_replace_ticker_table('SPX')
    exit(1)
    
    #x=db.execute_select('select current_schema();')
    #print(x)
    _=db.read_queries()
    db.execure_queries(_)
    print(_)
    exit(1)
    
    df=db.execute_select('select 1 as foo')   
    print(df)
    # make a dummy df 
    df=pd.DataFrame({'foo':[1,2,3],'bar':[4,5,6]})
    db.write_df(df)