###															###
###	No Generative AI was used in the writing of this code.	###	
###															###
import sys
import yaml
from loguru import logger
from pathlib import Path

logger_format = "{time:HH:mm:ss} | <lvl>{level}</lvl> | <lvl>{message}</lvl>"
logger.remove()
logger.add(sys.stdout, format=logger_format, level="INFO")

STYLES = ['CV', 'VCV', 'CVVC', 'VCCV']

def load_config(config_loc: Path) -> dict:
	try:
		with open(str(config_loc), 'r', encoding='utf-8') as c:
			config = yaml.safe_load(c.read())
			c.close()
		if not config['recording_style'] in STYLES:
			logger.error(f'UTACompiler does not support recording style {config['recording_style']}.')
			sys.exit(1)
		logger.info('Successfully loaded config file.')
		return config
	except yaml.YAMLError as e:
		logger.error(f'Unable to load config file: {e}')
		sys.exit(1)
	except Exception as e:
		logger.error(f'Unidentified error loading config: {e}')
		sys.exit(1)

def n_float(value) -> float:
	return float(f"{float(value):.3f}")