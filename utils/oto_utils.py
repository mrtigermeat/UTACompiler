###												###
###	No AI was used in the writing of this code. ###	
###												###
import sys
from pathlib import Path
from pydub import AudioSegment
from ftfy import fix_text
from itertools import islice
from tqdm import tqdm

from utils.utils import n_float
from utils.logger_utils import get_logger

logger = get_logger(level="INFO")

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