'''Set up logging, SOMTS-style'''

import logging

def setup_logger(logger_name, log_file, level=logging.INFO):
    '''Set up a logging instance to a file'''
    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter("\t".join(['%(asctime)s ' +
                                            '%(pathname)s:%(lineno)d',
                                            '%(levelname)s',
                                            '%(message)s',]))
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(file_handler)

    return logger
