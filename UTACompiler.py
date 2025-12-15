###															###
###	No Generative AI was used in the writing of this code.	###	
###															###
import sys
import os
import yaml
import random
import shutil
from pydub import AudioSegment
from pathlib import Path
from ftfy import fix_text
from tqdm import tqdm

root_dir = Path(__file__).parent.parent.resolve()
os.environ['PYTHONPATH'] = str(root_dir)
sys.path.insert(0, str(root_dir))

# UTACompiler specific imports
from utils.audio_utils import generate_tone, process_audiosegment, match_amplitude
from utils.utils import load_config, n_float
from utils.logger_utils import get_logger
from utils.oto_utils import load_oto, oto_chunker, reconstruct_oto, oto_condenser

logger = get_logger(level="INFO")

def encode(oto: list, config: dict, build_path: Path) -> list:
	logger.info('Encoding audio & automatically adjusting oto...')
	out_fn = build_path / 'src'
	new_oto = []
	encoding_enabled = config['encoding']['enabled']
	if not out_fn.exists():
		try:
			os.makedirs(str(out_fn), exist_ok=True)
		except Exception as e:
			logger.error(f'Unable to create folder {str(out_fn)}: {e}')
			sys.exit(1)

	audio_idx = 1
	pad_val = n_float(config['encoding']['pad_val'])
	recording_style = config['recording_style']

	for chunk in tqdm(oto_chunker(oto, config)):
		x = AudioSegment.empty()
		if config['encoding']['enabled']:
			t1 = generate_tone(config)
		else:
			t1 = AudioSegment.empty()
		x += t1
		lengths = []
		audio_fn = f"{audio_idx:05}.wav"
		for i, entry in enumerate(chunk):
			y = AudioSegment.from_file(fix_text(entry['wav_name']))
			y = process_audiosegment(y)

			start = n_float(entry['offset'])
			end = n_float(entry['cutoff'])
			length = n_float(len(y))

			# Adjust cutoff
			if end > 0:
				end = length - end
			else:
				end = start + (end * -1)

			if recording_style == 'CV' or pad_val == 0.0:
				offset = n_float(len(x))
				y_slice = y[start:end]
				cutoff = ((n_float(len(y_slice))) * -1) + 10
			else:
				offset = n_float(len(x)) + pad_val
				y_slice = y[start-pad_val:end+pad_val]
				y_slice = y_slice.fade_in(pad_val/4.0).fade_out(pad_val/4.0)
				cutoff = ((n_float(len(y_slice)) - pad_val) * -1) + 10

			x += y_slice

			if encoding_enabled and i < config['files']['glob'] - 1:
				x += generate_tone(config)

			new_oto.append({
				'alias': entry['alias'],
				'wav_name': str(audio_fn),
				'offset': offset,
				'consonant': n_float(entry['consonant']),
				'cutoff': cutoff,
				'preutt': n_float(entry['preutt']),
				'overlap': n_float(entry['overlap']),
			})

		audio_idx += 1

		try:
			x.export(
				out_fn / audio_fn,
				format='wav',
				parameters=['-acodec', 'pcm_s16le']
			)
		except Exception as e:
			logger.error(f'Unable to export audio file {str(audio_fn)}: {e}')
			sys.exit(1)
	return new_oto

def utacompiler(db_path: Path, config: dict) -> None:
	logger.success('UTACompiler: Compile & Encode your UTAU Voice Library.')
	seed = config['seed']

	db_path = Path(db_path)

	logger.info(f'Applying seed: {seed}')
	try:
		random.seed(int(seed))
	except:
		logger.info(f'Unable to apply seed. Using standard randomization instead.')

	build_path = db_path / 'UTACompilerOutput' / config['name']
	logger.info(f'Creating output folder: {str(build_path)}')
	if build_path.exists():
		shutil.rmtree(build_path)
	try:
		os.makedirs(str(build_path), exist_ok=True)
	except Exception as e:
		logger.error(f'Unable to create output folders: {e}')
		sys.exit(1)

	logger.info('Organizing DB...')
	for file in config['files']['keep_files']:
		file_fn = db_path / file
		try:
			new_path = build_path / file
			if not new_path.exists():
				shutil.copy(file_fn, f"{build_path}/{file}")
		except FileNotFoundError:
			pass
		except Exception as e:
			logger.error(f"Unable to move file {str(file_fn)}: {e}")

	for folder in config['files']['keep_folders']:
		folder_fn = db_path / folder
		try:
			new_folder = build_path / folder
			if not new_folder.exists():
				shutil.copytree(folder_fn, f"{build_path}/{folder}")
		except FileNotFoundError:
			pass
		except Exception as e:
			logger.error(f'Unable to move folder {str(file_fn)}: {e}')

	oto = []
	for pitch in config['files']['pitches']:
		logger.info(f'Parsing oto.ini for pitch: {pitch}')
		pitch_path = db_path / pitch
		pitch_oto = load_oto(pitch_path, config)
		oto.extend(pitch_oto)

	if config['files']['scramble']:
		oto = sorted(oto, key=lambda x: random.random())

	new_oto = encode(oto, config, build_path)

	if config['encoding']['optimize']:
		new_oto = oto_condenser(new_oto)

	reconstruct_oto(new_oto, config, build_path)
	logger.success('UTACompiler has completed your voice library. Please rigorously test to ensure everything is well.')

if __name__ == "__main__":
	import click

	@click.command(help='UTACompiler: Compile & Encode your UTAU Voice Library.')
	@click.argument('path', metavar='PATH')
	@click.option('--config', '-c', type=str, help='Define non-default location for utacompiler_config.yaml.')
	def main(path: str, config: str) -> None:
		db_path = Path(path)
		if config:
			config_loc = Path(config)
		else:
			config_loc = db_path / 'utacompiler_config.yaml'
		if not config_loc.exists():
			logger.error(f"Unable to locate configuration file in {str(config_loc)}. Please ensure your \'utacompiler_config.yaml\' file is in the root of the voicebank, or you define a custom path with \'-c\'.")
			sys.exit(1)
		config = load_config(config_loc)

		utacompiler(db_path, config)

	main()