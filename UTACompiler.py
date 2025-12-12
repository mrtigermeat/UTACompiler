###												###
###	No AI was used in the writing of this code. ###	
###												###
import sys
import os
import yaml
import random
import shutil
import numpy as np
from pydub import AudioSegment
from pathlib import Path
from loguru import logger
from ftfy import fix_text
from itertools import islice
from tqdm import tqdm

root_dir = Path(__file__).parent.parent.resolve()
os.environ['PYTHONPATH'] = str(root_dir)
sys.path.insert(0, str(root_dir))

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

def load_oto(pitch_path: Path, config: dict) -> list:
	oto_out = []
	try:
		with open(str(pitch_path / 'oto.ini'), 'r', encoding=config['files']['file_encoding']) as f:
			for line in f:
				fline = fix_text(line).rstrip()
				wav_name, remainder = fline.split('=')
				wav_path = pitch_path / wav_name
				alias, offset, consonant, cutoff, preutt, overlap = remainder.split(',')

				# cutoff fix to make shit easier
				if float(cutoff) > 0:
					x = AudioSegment.from_file(wav_path)
					cutoff = n_float(-((len(x) - (float(offset) + float(cutoff)))))

				oto_out.append({
						'alias': alias,
						'wav_name': str(wav_path),
						'offset': n_float(offset),
						'consonant': n_float(consonant),
						'cutoff': cutoff,
						'preutt': n_float(preutt),
						'overlap': n_float(overlap)
					})
			f.close()
		logger.info(f'Successfully read oto.ini in {str(pitch_path)}.')
		return oto_out
	except SyntaxError as e:
		logger.error(f'Unable to process oto because you did not select the proper file encoding in your configuration. {e}')
		sys.exit(1)

def oto_chunker(oto: list, config: dict) -> list:
	it = iter(oto)
	chunks = []
	while True:
		chunk = list(islice(it, config['files']['glob']))
		if not chunk:
			break
		chunks.append(chunk)
	return chunks

def match_amplitude(x: AudioSegment, target: float = -30.0) -> AudioSegment:
	change = target - x.dBFS
	return x.apply_gain(change)

def generate_tone(config: dict) -> AudioSegment:
	silence = AudioSegment.silent(duration=50)
	sig_type = random.choice(['sine', 'square', 'triangle'])
	freq = random.randint(config['encoding']['min_frq'], config['encoding']['max_frq'])
	dur = random.uniform(config['encoding']['min_dur'], config['encoding']['max_dur'])
	dur = round(dur, 3)
	dur /= 100
	volume = random.uniform(config['encoding']['min_vol'], config['encoding']['max_vol'])
	t = np.linspace(0, dur, int(44100 * dur), False)
	if sig_type == 'sine':
		gen_x = np.sin(2 * np.pi * freq * t) * volume
	elif sig_type == 'square':
		gen_x = np.sign(np.sin(2 * np.pi * freq * t)) * volume
	elif sig_type == 'triangle':
		gen_x = 2 * np.abs(2 * (t * freq * np.floor(t * freq * 0.5))) - 1
		gen_x *= volume
	x = (gen_x * 32767).astype(np.uint64)
	y = match_amplitude(AudioSegment(
			x.tobytes(),
			frame_rate=44100,
			sample_width=2,
			channels=1,
		))
	fade_amt = len(y) / 10
	y = y.fade_in(fade_amt).fade_out(fade_amt)
	return silence + y + silence

def process_audiosegment(x: AudioSegment) -> AudioSegment:
	x.set_channels(1)
	x.set_frame_rate(44100)
	return x.set_sample_width(2)

def encode_audio(oto: list, config: dict, build_path: Path) -> list:
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

			if end > 0:
				end = length - end
			else:
				end = start + (end * -1)

			if recording_style == 'CV' or pad_val == 0.0:
				offset = n_float(len(x))
				y_slice = y[start:end]
				cutoff = (n_float(len(y_slice))) * -1
			else:
				offset = n_float(len(x)) + pad_val
				y_slice = y[start-pad_val:end+pad_val]
				y_slice = y_slice.fade_in(pad_val).fade_out(pad_val)
				cutoff = (n_float(len(y_slice)) - pad_val) * -1

			x += y_slice

			if encoding_enabled and i < config['files']['glob'] - 1:
				t = generate_tone(config)
			else:
				t = AudioSegment.empty()

			x += t

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

def reconstruct_oto(new_oto: list, config: dict, build_path: Path) -> None:
	logger.info('Reconstructing oto file.')
	out_fn = build_path / 'src'
	try:
		with open(out_fn / 'oto.ini', 'w', encoding=config['files']['file_encoding']) as o:
			for i, entry in enumerate(tqdm(new_oto)):
				string = f"{entry['wav_name']}={entry['alias']},{entry['offset']},{entry['consonant']},{entry['cutoff']},{entry['preutt']},{entry['overlap']}"
				if i == 0:
					o.write(string)
				else:
					o.write('\n'+string)
			o.close()
		logger.success('Successfully exported oto.')
	except Exception as e:
		logger.error(f'Unable to reconstruct oto: {e}')
		sys.exit(1)

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

	new_oto = encode_audio(oto, config, build_path)
	reconstruct_oto(new_oto, config, build_path)
	logger.success('UTACompiler has completed your voice library. Please rigorously test to ensure everything is well.')

if __name__ == "__main__":
	import click

	@click.command(help='UTACompiler: Compile & Encode your UTAU Voice Library.')
	@click.argument('path', metavar='PATH')
	@click.option('--config', '-c', type=str, help='Define non-default location for utacompiler_config.yaml.')
	@click.option('--silent', '-s', is_flag=True, help='Turns off logger.')
	def main(path: str, config: str, silent: bool) -> None:
		if silent:
			logger.remove()
			logger.add(sys.stdout, format=logger_format, level="CRITICAL")

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