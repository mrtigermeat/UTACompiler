###															###
###	No Generative AI was used in the writing of this code.	###	
###															###
import sys
import os
import yaml
import shutil
from loguru import logger
from pathlib import Path

logger_format = "{time:HH:mm:ss} | <lvl>{level}</lvl> | <lvl>{message}</lvl>"
logger.remove()
logger.add(sys.stdout, format=logger_format, level="INFO")

STYLES = ['CV', 'VCV', 'CVVC', 'VCCV']

TEMP_PATH = Path('tmp')

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

def export_uar(db_path: Path, build_path: Path, config: dict) -> None:
	uar_base = [
		'type=voiceset',
		f'folder={config['name']}',
		f'contentsdir={config['name']}',
		f'description={config['name']} - Compiled by UTACompiler',
	]

	if not TEMP_PATH.exists():
		os.mkdir(TEMP_PATH)

	with open(TEMP_PATH/'install.txt', 'w', encoding='shift-jis') as o:
		o.write("\n".join(uar_base))
		o.close()

	shutil.copytree(build_path, TEMP_PATH/build_path.stem)

	try:
		export_name = config['name'].replace(' ', '_')
		shutil.make_archive(
			build_path/f'{export_name}',
			'zip',
			TEMP_PATH,
		)
		os.rename(build_path/f'{export_name}.zip', build_path.parent/f'{export_name}.uar')
	except Exception as e:
		logger.error(f'Unable to export .uar archive: {e}')

	try:
		shutil.rmtree(TEMP_PATH)
	except Exception as e:
		logger.error(f'unable to delete temporary directory: {e}')