###															###
###	No Generative AI was used in the writing of this code.	###	
###															###
import sys
from loguru import logger

def get_logger(level: str) -> logger:
	logger_format = "{time:HH:mm:ss} | <lvl>{level}</lvl> | <lvl>{message}</lvl>"
	logger.remove()
	logger.add(sys.stdout, format=logger_format, level="INFO")
	return logger