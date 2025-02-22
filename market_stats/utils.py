import datetime
import logging 
import os 
import pandas as pd 
def to_milliseconds(date_str):
    """Convert a date string (YYYY-MM-DD) to Binance timestamp (milliseconds)."""
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")  # Use datetime.datetime
    return int(dt.timestamp() * 1000)

def to_datetime(unixtimestamp):
    return pd.to_datetime(unixtimestamp,unit='ms')


def setup_logger(name,mode='w',fp=None):
    # Create a custom logger
    if fp is None:
        this_path=os.path.dirname(os.path.abspath(__file__))
        fp=os.path.join(fp)
    logger = logging.getLogger(name)

    # Set the level of logger to INFO
    logger.setLevel(logging.INFO)

    # Create handlers
    c_handler = logging.StreamHandler()
    fp=os.path.join(fp,f'{name}.log')
    f_handler = logging.FileHandler(fp,mode)

    # Set level of handlers to INFO
    c_handler.setLevel(logging.ERROR)
    f_handler.setLevel(logging.INFO)

    # Create formatters and add it to handlers
    format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(format)
    f_handler.setFormatter(format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger