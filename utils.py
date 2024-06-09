import logging
import os 
import functools
def setup_logger(name,fp='./',mode='w'):
    # Create a custom logger
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

def exception_logger(cls):
    class Wrapped(cls):
        def __init__(self, *args, **kwargs):
            #self.logger = logging.getLogger(cls.__name__)
            self.logger=setup_logger(cls.__name__,fp='./logs/',mode='w')
            super().__init__(*args, **kwargs)

        def __getattribute__(self, name):
            attr = super().__getattribute__(name)
            if callable(attr):
                @functools.wraps(attr)
                def wrapper(*args, **kwargs):
                    try:
                        return attr(*args, **kwargs)
                    except Exception as e:
                        self.logger.error(f"Exception occurred in {name}: {e}")
                        raise
                return wrapper
            else:
                return attr
    return Wrapped