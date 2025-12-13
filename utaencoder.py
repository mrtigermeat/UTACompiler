# UTAUEncoder - Written by tigermeat - https://tigermeat.xyz/#utaucomp
import sys
import os
import yaml
import random
import shutil
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize
from glob import glob
from pathlib import Path
from loguru import logger
from ftfy import fix_text
from tqdm import tqdm
from itertools import islice

root_dir = Path(__file__).parent.parent.resolve()
os.environ['PYTHONPATH'] = str(root_dir)
sys.path.insert(0, str(root_dir))

logger_format = "{time:HH:mm:ss} | <lvl>{level}</lvl> | <lvl>{message}</lvl>"
logger.remove()
logger.add(sys.stdout, format=logger_format, level="INFO")

def load_config(self, config_path: Path) -> dict:
	try:
		with open(str(config_path), 'r', encoding='utf-8') as c:
			config = yaml.safe_load(c.read())
			c.close()
		logger.info('Successfully loaded config file.')
		return config
	except yaml.YAMLError as e:
		logger.error(f'Unable to load config file: {e}')
		sys.exit(1)
	except Exception as e:
		logger.error(f'Unidentified error loading config: {e}')
		sys.exit(1)

def scrambler(self, indict: dict) -> dict:
	to_shuffle = list(indict.items())
	random.shuffle(to_shuffle)
	out_dict = dict(to_shuffle)
	return out_dict

def match_amplitude(self, x: AudioSegment, target: float = -30.0) -> AudioSegment:
	change = target - x.dBFS
	return x.apply_gain(change)

@logger.catch
def generate_tone(config: dict) -> AudioSegment:
	silence = AudioSegment.silent(duration=50)
	type = random.choice(['sine', 'square', 'triangle'])
	freq = random.randint(config['encoding']['min_frq'], config['encoding']['max_frq'])
	dur = random.uniform(config['encoding']['min_dur'], config['encoding']['max_dur'])
	dur = round(dur, 3)
	dur = dur / 100
	volume = random.uniform(config['encoding']['min_vol'], config['encoding']['max_vol'])
	t = np.linspace(0, dur, int(44100 * dur), False)
	if type == 'sine':
		gen_x = np.sin(2 * np.pi * freq * t) * volume
	elif type == 'square':
		gen_x = np.sign(np.sin(2 * np.pi * freq * t)) * volume
	elif type == 'triangle':
		gen_x = 2 * np.abs(2 * (t * freq * np.floor(t * freq + 0.5))) - 1
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

def load_oto(self, path: Path) -> dict:
	exp_dict = {}
	try:
		with open(str(path / 'oto.ini'), 'r', encoding=config['files']['file_encoding']) as f:
			for line in f:
				fline = fix_text(line).rstrip()
				wn, remainder = fline.split('=')
				wn = path / wn
				al, of, cn, co, pu, ol = remainder.split(',')

				if co > 0:
					x = AudioSegment.from_file(wn)
					co = -(n_float(len(x)) - (n_float(of) + n_float(co)))

				assert co >= 0

				exp_dict[al] = {
					'wn': str(wn),
					'of': n_float(of), #offset
					'cn': n_float(cn), #consonant
					'co': n_float(co), #cutoff
					'pu': n_float(pu), #preutterance
					'ol': n_float(ol), #overlap
				}
			f.close()
		logger.info(f'Successfully read OTO in {str(path)}.')
		return exp_dict
	except Exception as e:
		logger.warning(f'Unable to load OTO in {str(path)}: {e}')
		return {}

def oto_chunker(self, oto: dict) -> dict:
	it = iter(oto.items())
	chunks = []
	while True:
		chunk = dict(islice(it, config['files']['glob']))
		if not chunk:
			break
		chunks.append(chunk)
	return chunks

def process_audiosegment(self, x: AudioSegment) -> AudioSegment:
	x.set_channels(1)
	x.set_frame_rate(44100)
	return x.set_sample_width(2)

def n_float(self, inval) -> float:
	return float(f"{inval:03}")

def encode_audio(oto: dict, config: dict, build_path: Path) -> dict:
	# i rewrote this part from scratch like 14 times i s2g
	logger.info('Encoding Audio & Automatically adjusting OTO...')
	outfn = build_path / 'src'
	new_oto = {}
	if not outfn.exists():
		os.makedirs(str(outfn))
	pad_val = n_float(config['encoding']['padding'])
	audio_idx = 1
	for chunk in tqdm(oto_chunker(oto, config)):
		x = AudioSegment.empty()
		t1 = generate_tone(config)
		x += t1
		lengths = []
		audio_fn = f"{audio_idx:05}.wav"
		for k, v in chunk.items():
			y = AudioSegment.from_file(fix_text(v['wn']))
			y = process_audiosegment(y)

			# convert the oto values to the absolute position in the wav file 
			start = n_float(v['of'])
			end = n_float(v['co'])
			length = n_float(len(y))
			if end > 0:
				end = length - end
			else:
				end = start + (end * -1)
			offset = n_float(len(x)) + pad_val

			y_slice = y[start-pad_val:end+pad_val]
			y_slice = y_slice.fade_in(pad_val).fade_out(pad_val)
			cutoff = (n_float(len(y_slice)) - pad_val) * -1
			x += y_slice
			t = generate_tone(config)
			x += t

			new_oto[str(k)] = {
				'wn': str(audio_fn),
				'of': offset,
				'cn': n_float(v['cn']),
				'co': cutoff,
				'pu': n_float(v['pu']),
				'ol': n_float(v['ol']),
			}

		audio_idx += 1
		x.export(
			outfn / audio_fn,
			format='wav',
			parameters=['-acodec', 'pcm_s16le']
		)
	return new_oto

def reconstruct_oto(new_oto: dict, config: dict, build_path: Path) -> None:
	logger.info('Reconstructing OTO file.')
	outfn = build_path / 'src'
	
	with open(outfn / 'oto.ini', 'w', encoding=config['files']['file_encoding']) as o:
		for i, (k, v) in enumerate(tqdm(new_oto.items())):
			string = f"{v['wn']}={str(k)},{v['of']},{v['cn']},{v['co']},{v['pu']},{v['ol']}"
			if i == 0:
				o.write(string)
			else:
				o.write('\n'+string)
		o.close()
	logger.success('Successfully exported OTO file.')

def utaencoder(path: Path, config: Path) -> None:
	logger.success('UTAEncoder: Compile & Encoder your UTAU Voicebank.')
	config = load_config(config)
	seed = config['seed']

	logger.info(f'Applying seed: {seed}')
	try:
		random.seed(int(seed))
	except:
		logger.info(f'Unable to apply seed. Using standard randomization instead.')

	oto = {}
	vb_path = Path(path)
	build_path = vb_path / 'UTAEncoderOutput' / config['name']
	if not build_path.exists():
		try:
			os.makedirs(str(build_path), exist_ok=True)
		except Exception as e:
			logger.error(f"Unable to create output folders: {e}")
			sys.exit(1)

	# KEEP FILE/FOLDER LOGIC
	for file in config['files']['keep_files']:
		file_fn = vb_path / file
		try:
			shutil.copy(file_fn, f"{build_path}/{file}")
		except Exception as e:
			logger.error(f'Unable to move file {str(file_fn)}: {e}')
	for folder in config['files']['keep_folders']:
		folder_fn = vb_path / folder
		try:
			shutil.copytree(folder_fn, f"{build_path}/{folder}")
		except Exception as e:
			logger.error(f'Unable to move folder {str(file_fn)}: {e}')

	# LOAD OTO
	for pitch in config['files']['pitches']:
		pitch_path = vb_path / pitch
		pitch_oto = load_oto(pitch_path, config)
		oto.update(pitch_oto)
	if config['files']['scramble']:
		oto = scrambler(oto)

	# ENCODE AUDIO & BUILD NEW OTO
	new_oto = encode_audio(oto, config, build_path)
	reconstruct_oto(new_oto, config, build_path)

if __name__ == '__main__':
	import click

	@logger.catch
	@click.command(help='UTAEncoder: Compile & Encode your UTAU Voicebank.')
	@click.argument('path', metavar='PATH')
	def main(path: str):
		db_path = Path(path)
		config_loc = db_path / 'utaencoder_config.yaml'
		if not config_loc.exists():
			logger.error(f'Unable to locate configuration in {str(config_loc)}. Please ensure your \'utaencoder_config.yaml\' is there, properly configured.')
			sys.exit(1)
		utaencoder(db_path, config_loc)

	main()